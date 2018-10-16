import os
import logging
import logging.config  # needed when logging_config doesn't start with logging.config
from copy import copy

from moose.conf import settings
from moose.core import mail
from moose.core.management.color import color_style
from moose.utils.module_loading import import_string



# Default logging for Moose. This sends an email to the site admins on every
# HTTP 500 error. Depending on DEBUG, all other log records are either sent to
# the console (DEBUG=True) or discarded (DEBUG=False) by means of the
# require_debug_true filter.
DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'moose.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'moose.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'brief': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s',
        },
        'verbose': {
            'format': '%(asctime)s - [%(levelname)s]: (%(module)s.%(funcName)s) %(message)s',
        },
        'moose.console': {
            '()': 'moose.utils.log.ConsoleFormatter',
            'format': '[%(asctime)s] - %(module)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'WARNING',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'moose.console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(settings.BASE_DIR, 'moose.log')
        },
        'moose.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'moose': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
        'moose.server': {
            'handlers': ['moose.server'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


def configure_logging(logging_config, logging_settings):
    if logging_config:
        # First find the logging configuration function ...
        logging_config_func = import_string(logging_config)

        logging.config.dictConfig(DEFAULT_LOGGING)

        # ... then invoke it with the custom logging settings
        if logging_settings:
            logging_config_func(logging_settings)


class CallbackFilter(logging.Filter):
    """
    A logging filter that checks the return value of a given callable (which
    takes the record-to-be-logged as its only parameter) to decide whether to
    log a record.
    """
    def __init__(self, callback):
        self.callback = callback

    def filter(self, record):
        if self.callback(record):
            return 1
        return 0


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        return not settings.DEBUG


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        return settings.DEBUG


class ConsoleFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.style = color_style()
        super(ConsoleFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        msg = record.msg
        if record.levelname == 'DEBUG':
            # No color formatted for debugging message
            msg = msg
        elif record.levelname == 'INFO':
            msg = self.style.SUCCESS(msg)
        elif record.levelname == 'WARNING':
            msg = self.style.WARNING(msg)
        elif record.levelname == 'ERROR':
            msg = self.style.ERROR(msg)
        elif record.levelname == 'CRITICAL':
            msg = self.style.ERROR(msg)
        else:
            msg = msg

        record.msg = msg
        return super(ConsoleFormatter, self).format(record)
