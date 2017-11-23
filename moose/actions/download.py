# -*- coding: utf-8 -*-
import os
import urllib2
import threading
from Queue import Queue, Empty

from moose.conf import settings
from moose.utils._os import makeparents

import logging
logger = logging.getLogger(__name__)

class BaseDownloader(threading.Thread):
    """

    """
    def __init__(self, src_queue=None, dst_queue=None,
        set_up=None, tear_down=None, timeout=settings.DEFAULT_TIMEOUT):
        super(BaseDownloader, self).__init__()
        if set_up:
            self.src_queue = set_up()
        else:
            self.src_queue = src_queue if src_queue else Queue()

        self.tear_down = tear_down
        if not tear_down:
            self.dst_queue = dst_queue if dst_queue else Queue()

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
            except Empty as e:
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
        self.failed_list = []

    def __str__(self):
        return 'Download Result: OK: %d, FAILED: %d' % (self.nok, self.nfail)


def download(urls, dirpath, stat, overwrite=False):
    src_queue = Queue()

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

    downloader = BaseDownloader(src_queue=src_queue, tear_down=write)
    downloader.setDaemon(True)
    downloader.start()

    for task in urls:
        url, filepath = task
        if os.path.exists(filepath) and not overwrite:
            continue
        src_queue.put(task)

    src_queue.join()
