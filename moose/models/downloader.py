# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import socket
import Queue
import urllib2

from moose.utils._os import makedirs, makeparents, safe_join
from moose.utils.encoding import force_bytes
from moose.conf import settings

"""
Provides an uniform interface with multithreading, but in a blocked way.
The reason we provide the blocked worker is to offer a way to debug,
espacially when using actions like `export`.
"""
if settings.DEBUG:
    import dummy_threading as _threading
else:
    try:
        import threading as _threading
    except ImportError:
        import dummy_threading as _threading

lock = _threading.Lock()

import logging
logger = logging.getLogger(__name__)


class DownloadWorker(_threading.Thread):
    def __init__(self, queue, callback, stats, timeout, overwrite=False):
        super(DownloadWorker, self).__init__()
        self.queue     = queue
        self.callback  = callback
        # a mutex to count in threads
        self.stats     = stats
        self.timeout   = timeout
        self.overwrite = overwrite

    def run(self):
        while True:
            try:
                data_model = self.queue.get(timeout=self.timeout)
                data = self.fetch(data_model.filelink, data_model.retry)

                if data != None:
                    self.write(data, data_model.dest_filepath)
                    self.callback(data_model)
                    self.stats.inc_value("download/ok")
                else:
                    if data_model.retry > 0:
                        data_model.retry -= 1
                        self.queue.put(data_model)
                        self.stats.inc_value("download/retry")
                    else:
                        self.stats.inc_value("download/failed")

                self.queue.task_done()

            except Queue.Empty as e:
                break

    def fetch(self, url, retry):
        data = None
        warn = logger.error if retry == 0 else logger.info

        try:
            response = urllib2.urlopen(url, timeout=self.timeout)
            data = response.read()
        except urllib2.HTTPError, e:
            self.stats.inc_value("download/http_error")
            warn('falied to connect to %s, may for %s' % (url, e.reason))
        except urllib2.URLError, e:
            self.stats.inc_value("download/url_error")
            warn('unable to open url %s for %s' % (url, e.reason))
        except socket.error, e:
            self.stats.inc_value("download/socket_error")
            warn('socket error: %s' % url)
        return data

    def write(self, data, filepath):
        if os.path.exists(filepath):
            self.stats.inc_value("download/conflict")
            if not self.overwrite:
                return

        lock.acquire()
        makeparents(filepath)
        lock.release()

        with open(filepath, 'wb') as f:
            f.write(data)
        return


class ModelDownloader(object):
    def __init__(self, callback, stats, timeout=None, overwrite=False, nworkers=10):
        self.queue     = Queue.Queue()
        self.callback  = callback
        self.stats     = stats
        self.timeout   = timeout or settings.DEFAULT_TIMEOUT
        self.overwrite = overwrite
        # Run in one loop if setting DEBUG mode
        self.nworkers  = nworkers if not settings.DEBUG else 1

    def start(self):
        for i in range(self.nworkers):
            worker = DownloadWorker(self.queue, self.callback, self.stats, \
                        self.timeout, self.overwrite)
            worker.setDaemon(True)
            worker.start()

    def add_task(self, data_model):
        try:
            data_model.retry = 3
            self.queue.put(data_model)
        except Queue.Full as e:
            logger.error('Try to put an element in a full queue.')
            raise e

    def join(self):
        self.queue.join()
