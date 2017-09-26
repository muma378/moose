# -*- coding: utf-8 -*-
import os
import fnmatch


def ivisit(src, dst=None, pattern=None, ignorecase=True):
    """
    A iterator to find all files in path `src` and match the Unix shell-like
    `pattern` if provided. The value of `pattern` could be a string or a tuple,
    and would perform a case-sensitive comparision if `ignorecase` was set
    to False.

    Details for unix shell-like wildcards can be seen from:
        https://docs.python.org/2/library/fnmatch.html#module-fnmatch

    If `dst` was provided, returns a pair consists of source path and
    destination with sub-directories. For example, if `src` was set to '/a'
    `dst` was set to '/b', while a file was located at '/a/c/d.txt', will
    yield a tuple ('/a/c/d.txt', '/b/c/d.txt')
    """
    # syntax sugar, converts string to a tuple with one element
    if isinstance(pattern, str) or isinstance(pattern, unicode):
        pattern = (pattern, )
    # defines the function anymatch
    if pattern:
        if ignorecase:
            pattern = [p.lower() for p in pattern]
            matchfn = lambda s, p: fnmatch.fnmatch(s.lower(), p)
        else:
            matchfn = fnmatch.fnmatch
        # test if there was any one matched a pattern in the list
        anymatch = lambda s, ps: any([matchfn(s, p) for p in ps])
    else:
        # returns True always
        anymatch = lambda s, ps: True

    # traverse the source path
    for dirpath, dirnames, filenames in os.walk(src):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if anymatch(filepath, pattern):
                # if `dst` was set, returns a pair
                if dst:
                    relpath = os.path.relpath(filepath, src)
                    yield (filepath, os.path.join(dst, relpath))
                else:
                    yield filepath
