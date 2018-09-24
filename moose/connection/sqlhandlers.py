# -*- coding: utf-8 -*-
# database.py - provides uniform interfaces to query or insert the sql database
# authors: Liu Size, Xiao Yang<xiaoyang0117@gmail.com>
# date: 2016.01.28
from __future__ import unicode_literals

import sys
import time
import random

from moose.core.teminal import stdout
from moose.core.exceptions import ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from moose.conf import settings

import logging
logger = logging.getLogger(__name__)


class BaseSQLHandler(object):
    """
    Interface class for all SQL database opreations.
    """
    db_name = None

    def __init__(self, settings_dict):
        self.settings_dict = settings_dict
        self._conn = self.get_connection(settings_dict)
        self._cursor = None

    def get_connection(self, settings_dict):
        conn_cnt = 0
        while conn_cnt < settings.DB_CONN_MAX_TIMES:
            try:
                conn = self._connect(settings_dict):
                stdout.success("Connection to {} established.".format(self.db_name))
            except ConnectionTimeout as e:
                conn_cnt += 1
                interval = random.randint(0, settings.DB_CONN_MAX_INTERVAL)
                stdout.warn(
                    "Connection timeout to {}: {}\nWill retry to connect in {} \
                    seconds.".format(self.db_name, str(e), interval))
                time.sleep(interval)

        stdout.error("Unable to establish connection to '{}'".format(self.db_name))
        raise ImproperlyConfigured()

    def _connect(self, settings_dict):
        """
        Entry for subclass to define how to connect to database serverself.
        Raises 'ConnectionTimeout' error if failed not for fatal error.
        """
        raise NotImplementedError("Subclass of 'BaseSQLHandler' must provide method _connect().")

    def close(self):
        stdout.debug("Closing connection to {}.".format(self.db_name))
        try:
            self._close()
        except AttributeError, e:
            stdout.debug("Connection was closed already.")
        else:
            self._conn = None
            self._cursor = None
            stdout.debug("Connection closed.")

    def _close(self):
        """
        Entry for subclass to define closing connection method.
        """
        self._conn.close()

    def _get_cursor(self):
        """
        Entry for subclass to provide the cursor of connection.
        """
        return self._conn.cursor()

    def exec_query(self, operation):
        if not operation:
            stdout.error("No operation specified.")
            raise SuspiciousOperation

        try:
            self._cursor = self._get_cursor()
            stdout.info("Executing the operation:\n\t'{}'.".format(operation))
            self._cursor.execute(operation)
            result = self._cursor.fetchall()
        except Exception as e:
            stdout.error("Query failed: '{}'.".format(str(e)))
            return None

        stdout.info("Query successed.")
        return result

    def exec_commit(self, operation):
        if not operation:
            stdout.error("No operation specified.")
            raise SuspiciousOperation

        try:
            self._cursor = self._get_cursor()
            stdout.warn("Executing the operation:\n\t'{}'.".format(operation))
            self._cursor.execute(operation)
            self._conn.commit()
            naffected =  self._cursor.rowcount
        except Exception as e:
            stdout.error("Operation failed: '{}'.".format(str(e)))
            return None

        stdout.info("Operation successed with '{}' rows affected.".format(naffected))
        return naffected

    def exec_many(self, operation, params_seq):
        raise NotImplementedError("Database you use didn't provid method 'exec_many()' yet.")


class SQLServerHandler(BaseSQLHandler):
    """
    SQL database handler for sql server.
    """

    db_name = 'SQL Server'

    def _connect(self, settings_dict):
        import pymssql

        stdout.debug(
            "Trying to connect to SQLServer servered on '%s:%s'...".format(
            settings_dict['HOST'], settings_dict['PORT']))

        conn = None
        try:
            conn = pymssql.connect(
                host=settings_dict['HOST'],
                port=settings_dict['PORT'],
                user=settings_dict['USER'],
                password=settings_dict['PASSWORD'],
                database=settings_dict['DATABASE'],
                charset=settings_dict['CHARSET'],
                timeout=settings.DB_CONN_TIMEOUT,
            )
        except (pymssql.InterfaceError, pymssql.OperationalError) as e:
            stdout.error(e.message)
            raise ImproperlyConfigured("Failed to connect to SQL database '%s'." % settings_dict['HOST'])
        except KeyError as e:
            stdout.error(
                "Fields missing, please check %s was in settings." % e.message)
            raise ImproperlyConfigured("Fields missing: %s" % e.message)
        return conn

    def exec_many(self, sql_commit, rows):
        if not operation:
            stdout.error("No operation specified.")
            raise SuspiciousOperation

        try:
            self._cursor = self._get_cursor()
            stdout.warn("Executing the operation:\n\t'{}'.".format(operation))
            # see ref: http://pymssql.org/en/stable/pymssql_examples.html
            self._cursor.executemany(operation, params_seq)
            self._conn.commit()
            naffected =  self._cursor.rowcount
        except Exception as e:
            stdout.error("Operation failed: '{}'.".format(str(e)))
            return None

        stdout.info("Operation successed with '{}' rows affected.".format(naffected))
        return naffected
