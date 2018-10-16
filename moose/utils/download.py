# -*- coding: utf-8 -*-
import os
import Queue
import socket
import urllib2
import httplib
import threading

from moose.conf import settings
from moose.utils._os import makeparents

import logging
logger = logging.getLogger(__name__)

class PipelineDownloader(threading.Thread):
    """
    Class to handle downloading jobs in a multi-threading way,
    it performs like a "pipeline", which defines an INPUT end and
    an OUTPUT end. They both are queues to accept data from the
    last node and send to the following one.

    Meanwhile, we defined functions `set_up` and `tear_down` to
    generate and digest data.
    """
    def __init__(self, src_queue=None, dst_queue=None,
        set_up=None, tear_down=None, timeout=settings.DEFAULT_TIMEOUT):
        super(PipelineDownloader, self).__init__()
        if set_up:
            self.src_queue = set_up()
        else:
            self.src_queue = src_queue if src_queue else Queue.Queue()

        self.tear_down = tear_down
        if not tear_down:
            self.dst_queue = dst_queue if dst_queue else Queue.Queue()

        self.timeout = timeout

    def run(self):
        while True:
            try:
                task = self.src_queue.get(timeout=self.timeout)
                result = self.process(task)
                if self.tear_down:
                    self.tear_down(result)
                else:
                    self.dst_queue.put(result, timeout=self.timeout)
                self.src_queue.task_done()
            except Queue.Empty as e:
                break

    def process(self, task):
        url, name = task
        data = None
        retry = 3
        while retry > 0:
            try:
                response = urllib2.urlopen(url, timeout=self.timeout)
                data = response.read()
                return (data, name)
            except urllib2.HTTPError, e:
                retry -= 1
                if retry == 0:
                    logger.error('falied to connect to %s, may for %s' % (url, e.reason))
            except urllib2.URLError, e:
                retry -= 1
                if retry == 0:
                    logger.error('unable to open url %s for %s' % (url, e.reason))
            except socket.error, e:
                retry -= 1
                if retry == 0:
                    logger.error('socket error: %s' % url)
            except httplib.BadStatusLine, e:
                retry -= 0.5
                if retry == 0:
                    logger.error('An unknown http status returned: %s' % url)

        return None

class DownloadStat:
    def __init__(self):
        self.nok = 0
        self.nfail = 0
        self.nconflict = 0
        self.failed_list = []

    def __str__(self):
        return 'Download Result: OK: %d, FAILED: %d' % (self.nok, self.nfail)


def download(urls, dirpath, workers=10, overwrite=False):
    """
    A convenient way to download files to a directory. It returns a
    "DownloadStat" object to report the statistic of result.

    `urls`
        A list of pair consists of filelink and relpath.
        ('http://www.abc.com/path/to/location.jpg', 'path/to/location.jpg')

    `dirpath`
        Path to put all downloaded files.

    `workers`
        The number of threads.

    `overwrite`
        A flag to indicate whether to overwrite files existed.
    """
    stat = DownloadStat()
    src_queue = Queue.Queue()
    lock = threading.Lock()

    def write(response):
        if not response:
            stat.nfail += 1
        else:
            data, name = response
            dst_file = os.path.join(dirpath, name)

            lock.acquire()
            makeparents(dst_file)
            lock.release()

            with open(dst_file, 'w') as f:
                f.write(data)
            stat.nok += 1

    for _ in range(workers):
        downloader = PipelineDownloader(src_queue=src_queue, tear_down=write)
        downloader.setDaemon(True)
        downloader.start()

    for task in urls:
        url, filepath = task
        if os.path.exists(filepath) and not overwrite:
            continue
        src_queue.put(task)

    src_queue.join()
    return stat
