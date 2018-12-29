# -*- coding: utf-8 -*-
# database.py - provides uniform interfaces to query or insert the sql database
# authors: Liu Size, Xiao Yang<xiaoyang0117@gmail.com>
# date: 2016.01.28
from __future__ import unicode_literals

import sys
import time
import random
import string

from moose.core.terminal import stdout
from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from moose.conf import settings

import logging
logger = logging.getLogger(__name__)


class BaseSQLHandler(object):
    """
    Interface for all SQL database drivers. PEP-249(https://www.python.org/dev
    /peps/pep-0249/) defines API to encourage similarity between the Python
    modules that are used to access databases.
    Unfortunately, many database drivers were writen before the sepcification,
    to provide a uniform interface, different drivers were wrapped. Therefore,
    if the python module was writen as `PEP-249`, the `BaseSQLHandler` has
    already implemented almost all features need.
    """
    db_name = None
    table_alias_name   = "TABLE_ALIAS"

    def __init__(self, settings_dict):
        if not isinstance(settings_dict, dict):
            raise ImproperlyConfigured(
                "Argument `settings_dict` is the configure for sql drivers, "
                "which must be an instance of `dict`.")

        self.settings_dict = settings_dict
        self._conn = self.get_connection(settings_dict)

        if settings_dict.get(self.table_alias_name):
            self._table_alias = settings_dict[self.table_alias_name]
        else:
            raise ImproperlyConfigured(\
                "Key missing: `{}` is required to provide a map of "
                "alias to table names in the database.".format(self.table_alias_name))

        self._cursor = None

    def get_connection(self, settings_dict):
        if settings_dict.get('HOST') and settings_dict.get('PORT'):
            stdout.debug(
                "Trying to connect to {} servered on '{}:{}'...".format(
                self.db_name, settings_dict['HOST'], settings_dict['PORT'])
                )

        conn_cnt = 0
        while conn_cnt < settings.DB_CONN_MAX_TIMES:
            try:
                conn = self._connect(settings_dict)
                stdout.success("Connection to {} established.".format(self.db_name))
                return conn
            except ConnectionTimeout as e:
                conn_cnt += 1
                interval = random.randint(0, settings.DB_CONN_MAX_INTERVAL)
                stdout.warn(
                    "Connection timeout to {}: {}\nWill retry to connect in {} \
                    seconds.".format(self.db_name, str(e), interval))
                time.sleep(interval)
            except KeyError as e:
                # May raise when resolving the settings dict
                stdout.error(
                    "Fields missing, check '{}' was set.".format(str(e)))
                raise ImproperlyConfigured("Fields missing: {}".format(str(e)))

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
        except AttributeError as e:
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

    def execute(self, operation, operator, *args):
        if not operation:
            stdout.error("No operation specified.")
            raise SuspiciousOperation

        try:
            cursor = self._get_cursor()
            operation = string.Template(operation).substitute(self._table_alias)
            stdout.info("Executing the operation:\n\t'{}'.".format(operation))
            result = operator(cursor, operation, *args)
        # TODO: defines more detailed errors
        except Exception as e:
            stdout.error("Operation failed: '{}'.".format(str(e)))
            return None

        stdout.info("Operation succeed.")
        return result


    def exec_query(self, operation):
        """
        Shortcuts to execute query operations. These operations are
        always executed with `fetch*()` methods
        """
        def _operator(cursor, operation, *args):
            cursor.execute(operation)
            result = cursor.fetchall()
            return result

        return self.execute(operation, _operator)


    def exec_commit(self, operation):
        """
        Shortcuts to execute non-query operations, such as: INSERT
        UPDATE and DELETE. These operations are always executed with
        `commit()` methods
        """
        def _operator(cursor, operation, *args):
            cursor.execute(operation)
            self._conn.commit()
            naffected = cursor.rowcount
            stdout.info("Operation completed with '{}' rows affected.".format(naffected))
            return naffected

        return self.execute(operation, _operator)

    def exec_many(self, operation, params_seq):
        """
        Entry for subclass to execute many operations in a request.
        """
        raise NotImplementedError("Database you use didn't provid method 'exec_many()' yet.")
