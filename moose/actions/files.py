# -*- coding: utf-8 -*-
import os
import logging

logger = logging.getLogger(__name__)

class IllegalFileObject(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class FileObject(object):
    """
    Class represents a file object, it contains several properties,
    such as size, ctime, atime and etc.

    Derived class defines custom context by implementing `_get_context`.
    """
    LABEL_CHOICES = []

    def __init__(self, filepath):
        self.filepath = filepath
        dirname, self.filename = os.path.split(self.filepath)

        self._get_context(dirname)
        self._get_meta()

    def __str__(self):
        return npath(self.filepath)

    def __unicode__(self):
        return self.filepath

    @property
    def group(self):
        raise NotImplementedError("Subclass of FileObject must provide group() method.")

    @property
    def label(self):
        if self.LABEL_CHOICES:
            for label in self.LABEL_CHOICES:
                if label in self.filename:
                    return label
            logger.error("[InvalidName] Unrecognized label in %s" % self.filepath)
            raise IllegalFileObject("[InvalidName] Unrecognized label in %s" % self.filepath)
        else:
            raise NotImplementedError("Subclass of FileObject must provide either `LABEL_CHOICES` or `label()` method.")

    def _get_context(self, dirname):
        pass

    def _get_meta(self):
        stat = os.stat(self.filepath)
        self.size  = stat.st_size
        self.atime = stat.st_atime
        self.mtime = stat.st_mtime
        self.ctime = stat.st_ctime

    def _time2str(self, secs):
        return time.strftime('%d %b %Y %H:%M:%S', time.gmtime(secs))

    @property
    def py_ctime(self):
        return datetime.fromtimestamp(self.ctime)

    def to_row(self):
        return (
            self.filename,
            sizeof_fmt(self.size),
            self._time2str(self.atime),
            self._time2str(self.mtime),
            self._time2str(self.ctime)
            )
