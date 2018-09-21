from __future__ import unicode_literals

import os
import sys
import tempfile
from os.path import abspath, dirname, isabs, join, normcase, normpath, sep

import six

from moose.core.exceptions import SuspiciousFileOperation
from moose.utils.encoding import force_text
from moose.conf import settings

if six.PY2:
    fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()


def upath(path):
    """
    Always return a unicode path.
    """
    if six.PY2 and not isinstance(path, six.text_type):
        return path.decode(fs_encoding)
    return path


def npath(path):
    """
    Always return a native path, that is unicode on Python 3 and bytestring on
    Python 2.
    """
    if six.PY2 and not isinstance(path, bytes):
        return path.encode(fs_encoding)
    return path


def safe_join(base, *paths):
    """
    Join one or more path components to the base path component intelligently.
    Return a normalized, absolute version of the final path.

    Raise ValueError if the final path isn't located inside of the base path
    component.
    """
    base = force_text(base)
    paths = [force_text(p) for p in paths]
    final_path = abspath(join(base, *paths))
    base_path = abspath(base)
    # Ensure final_path starts with base_path (using normcase to ensure we
    # don't false-negative on case insensitive operating systems like Windows),
    # further, one of the following conditions must be true:
    #  a) The next character is the path separator (to prevent conditions like
    #     safe_join("/dir", "/../d"))
    #  b) The final path must be the same as the base path.
    #  c) The base path must be the most root path (meaning either "/" or "C:\\")
    if (not normcase(final_path).startswith(normcase(base_path + sep)) and
            normcase(final_path) != normcase(base_path) and
            dirname(normcase(base_path)) != normcase(base_path)):
        raise SuspiciousFileOperation(
            'The joined path ({}) is located outside of the base path '
            'component ({})'.format(final_path, base_path))
    return final_path


def symlinks_supported():
    """
    Return whether or not creating symlinks are supported in the host platform
    and/or if they are allowed to be created (e.g. on Windows it requires admin
    permissions).
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        original_path = os.path.join(temp_dir, 'original')
        symlink_path = os.path.join(temp_dir, 'symlink')
        os.makedirs(original_path)
        try:
            os.symlink(original_path, symlink_path)
            supported = True
        except (OSError, NotImplementedError):
            supported = False
        return supported


WIN_PATH_SEP = '\\'
POSIX_PATH_SEP = '/'

def ppath(path):
    """
    Return a posix-style path, whose separator of path is '/'.
    """
    return path.replace(WIN_PATH_SEP, POSIX_PATH_SEP)


def wpath(path):
    """
    Return a windows-style path, whose separator of path is '\\'.
    """
    return path.replace(POSIX_PATH_SEP, WIN_PATH_SEP)


def posixpath(path):
    """
    Return a posix-style path, whose separator of path is '/'.
    """
    return path.replace(WIN_PATH_SEP, POSIX_PATH_SEP)


def normpath(path):
    """
    Converts to the local filesystem, but keeps letters case.
    """
    if settings.IS_WINDOWS:
        return wpath(path)
    else:
        return ppath(path)


def makedirs(dirpath):
    """
    Creates the directory as dirpath indicates. Do not raise an
    exception if the dirpath was existed already.
    """
    if not os.path.exists(dirpath):
    	os.makedirs(dirpath)
    return dirpath

def makeparents(filepath):
    """
    Creates directoriea for a filepath.
    """
    makedirs(os.path.dirname(filepath))
    return filepath
