# -*- coding: utf-8 -*-
"""
This module provides a pseudo terminal to redirects messages.
"""
import sys
import logging

from moose.core.color import make_style, no_style, supports_color
from moose.utils.termcolors import parse_color_setting

class BaseTerminal(object):
    """
    Base class of terminals, defines common interfaces for different
    terminals.
    """
    def DEBUG(self, message):
        raise NotImplementedError

    def INFO(self, message):
        raise NotImplementedError

    def WARNING(self, message):
        raise NotImplementedError

    def ERROR(self, message):
        raise NotImplementedError


class Console(BaseTerminal):
    """
    Outputs string to console with different style rendered.
    """
    stdout = sys.stdout

    def __init__(self, color_config_string=None):
        if not supports_color():
            self._style = no_style()
        self._style = make_style(color_config_string)

    def write(self, output):
        self.stdout.write(output+'\n')

    def DEBUG(self, message):
        self.write(self._style.SUCCESS(message))

    def INFO(self, message):
        self.write(self._style.SUCCESS(message))

    def WARNING(self, message):
        self.write(self._style.NOTICE(message))

    def ERROR(self, message):
        self.write(self._style.ERROR(message))


class Logger(BaseTerminal):
    """
    Writes text to files, format the string to
    """
    def __init__(self, logging_settings):
        

    def DEBUG(self, message):
        self.logger.debug(message)

    def INFO(self, message):
        self.logger.info(message)

    def WARNING(self, message):
        self.logger.warning(message)

    def ERROR(self, message):
        self.logger.error(message)
