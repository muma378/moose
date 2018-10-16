# -*- coding: utf-8 -*-
# A standard output wrapper, defines whether (according to the verbose level)
# and what style (according to colors defined) uses to output

import sys

from moose.utils.encoding import force_str
from moose.core.management.color import color_style
from moose.core.exceptions import ImproperlyConfigured

style  = color_style()


class OutputWrapper(object):
    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, verbose):
        if verbose in [0, 1, 2, 3]:
            self._verbose = verbose
        elif verbose == None:
            self._verbose = 1
        else:
            raise ImproperlyConfigured("Verbose level was ought to be set from "
                                        "0 to 3, but got %s." % verbose)

    @property
    def style_func(self):
        return self._style_func

    @style_func.setter
    def style_func(self, style_func):
        if style_func and self.isatty():
            self._style_func = style_func
        else:
            self._style_func = lambda x: x

    def __init__(self, out, verbose=None, style_func=None, ending='\n'):
        self._out = out
        self.verbose = verbose
        self.style_func = style_func
        self.ending = ending

    def __getattr__(self, name):
        return getattr(self._out, name)

    def isatty(self):
        return hasattr(self._out, 'isatty') and self._out.isatty()

    def write(self, msg, verbose=1, style_func=None, ending=None):
        if self.verbose >= verbose:
            # outputs only if the verbose level of running
            # larger than the defined one
            ending = self.ending if ending is None else ending
            if ending and not msg.endswith(ending):
                msg += ending
            style_func = style_func or self.style_func
            self._out.write(force_str(style_func(msg)))

    def debug(self, msg):
        self.write(msg, verbose=3, style_func=style.NORMAL)

    def info(self, msg):
        self.write(msg, verbose=2, style_func=style.NORMAL)

    def warn(self, msg):
        self.write(msg, verbose=1, style_func=style.WARNING)

    def success(self, msg):
        self.write(msg, verbose=1, style_func=style.SUCCESS)

    def error(self, msg):
        self.write(msg, verbose=0, style_func=style.ERROR)


stdout = OutputWrapper(sys.stdout)
stderr = OutputWrapper(sys.stderr, style_func=style.ERROR)
