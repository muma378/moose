# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import MySQLdb as mysqldb

from .sqlhandler import BaseSQLHandler
from moose.core.terminal import stdout
from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from moose.conf import settings

import logging
logger = logging.getLogger(__name__)


class MySQLHandler(BaseSQLHandler):
    """
    SQL database handler for mysql.
    """
    db_name = 'MySQL'

    def _connect(self, settings_dict):
        try:
            conn = mysqldb.connect(
                host=settings_dict['HOST'],
                port=settings_dict['PORT'],
                user=settings_dict['USER'],
                passwd=settings_dict['PASSWORD'],
                db=settings_dict['DATABASE'],
                charset=settings_dict['CHARSET'],
                connect_timeout=settings.DB_CONN_TIMEOUT
                )
        except (mysqldb.InternalError, mysqldb.OperationalError) as e:
            stdout.warn(str(e))
            raise ConnectionTimeout
        return conn
