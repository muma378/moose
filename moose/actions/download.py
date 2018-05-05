# -*- coding: utf-8 -*-
import os
import Queue
import urllib2
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
        super(BaseDownloader, self).__init__()
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
        try:
            response = urllib2.urlopen(url, timeout=self.timeout)
            data = response.read()
            return (data, name)
        except urllib2.HTTPError, e:
            logger.error('falied to connect to %s, may for %s' % (url, e.reason))
        except urllib2.URLError, e:
            logger.error('unable to open url %s for %s' % (url, e.reason))


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

    def write(response):
        if not response:
            stat.nfail += 1
        else:
            data, name = response
            dst_file = os.path.join(dirpath, name)
            makeparents(dst_file)
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

class DownloadWorker(threading.Thread):
    def __init__(self, queue, callback, stat, timeout, overwrite=False):
        super(DownloadWorker, self).__init__()
        self.queue     = queue
        self.callback  = callback
        # a mutex to count in threads
        self.stat      = stat
        self.timeout   = timeout
        self.overwrite = overwrite

    def run(self):
        while True:
            try:
                data_model = self.queue.get(timeout=self.timeout)
                data = self.fetch(data_model.filelink)
                self.write(data, data_model.dest_filepath)
                self.callback(data_model)
                self.queue.task_done()
                self.stat.nok += 1
            except Queue.Empty as e:
                break

    def fetch(self, url):
        try:
            response = urllib2.urlopen(url, timeout=self.timeout)
            data = response.read()
            return data
        except urllib2.HTTPError, e:
            self.stat.nfail += 1
            logger.error('falied to connect to %s, may for %s' % (url, e.reason))
        except urllib2.URLError, e:
            self.stat.nfail += 1
            self.stat.failed_list.append(url)
            logger.error('unable to open url %s for %s' % (url, e.reason))


    def write(self, data, filepath):
        if os.path.exists(filepath):
            self.stat.nconflict += 1
            if not self.overwrite:
                return

        makeparents(filepath)
        with open(filepath, 'w') as f:
            f.write(data)
        return


class DataModelDownloader(object):
    def __init__(self, callback, output, timeout=None, overwrite=False, nworkers=10):
        self.queue = Queue.Queue()
        self.stat = DownloadStat()
        self.output = output
        self.callback = callback
        self.timeout = timeout or settings.DEFAULT_TIMEOUT
        self.overwrite = overwrite
        self.nworkers = nworkers

    def start(self):
        for i in range(self.nworkers):
            worker = DownloadWorker(self.queue, self.callback, self.stat, \
                        self.timeout, self.overwrite)
            worker.setDaemon(True)
            worker.start()

    def add_task(self, data_model):
        try:
            self.queue.put(data_model)
        except Queue.Full as e:
            logger.error('Try to put an element in a full queue.')
            raise e

    def join(self):
        self.queue.join()
