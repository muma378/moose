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
    Interface for all SQL database drivers. PEP-249(https://www.python.org/dev
    /peps/pep-0249/) defines API to encourage similarity between the Python
    modules that are used to access databases.
    Unfortunately, many database drivers were writen before the sepcification,
    to provide a uniform interface, different drivers were wrapped. Therefore,
    if the python module was writen as `PEP-249`, the `BaseSQLHandler` has
    already implemented almost all features need.
    """
    db_name = None

    def __init__(self, settings_dict):
        self.settings_dict = settings_dict
        self._conn = self.get_connection(settings_dict)
        self._cursor = None

    def get_connection(self, settings_dict):
        stdout.debug(
            "Trying to connect to {} servered on '{}:{}'...".format(
            self.db_name, settings_dict['HOST'], settings_dict['PORT'])
            )
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
            except KeyError as e:
                # May raise when resolving the settings dict
                stdout.error(
                    "Fields missing, check '{}' was set.".format(e.message))
                raise ImproperlyConfigured("Fields missing: {}".format(e.message))

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

    def execute(self, operation, operator, *args):
        if not operation:
            stdout.error("No operation specified.")
            raise SuspiciousOperation

        try:
            cursor = self._get_cursor()
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


class SQLServerHandler(BaseSQLHandler):
    """
    SQL database handler for sql server.
    """

    db_name = 'SQLServer'

    def _connect(self, settings_dict):
        import pymssql

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
        # More details on error of python database api, see ref:
        # https://www.python.org/dev/peps/pep-0249/
        except (pymssql.InternalError, pymssql.OperationalError) as e:
            stdout.warn(e.message)
            raise ConnectionTimeout
        return conn

    def exec_many(self, operation, params_seq):

        def _operator(cursor, operation, *args):
            if len(args) == 1:
                params_seq = args[0]
            else:
                raise SuspiciousOperation
            # see ref: http://pymssql.org/en/stable/pymssql_examples.html
            cursor.executemany(operation, params_seq)
            self._conn.commit()
            naffected = cursor.rowcount
            stdout.info("Operation completed with '{}' rows affected.".format(naffected))
            return naffected

        return self.execute(operation, _operator, params_seq)

class MySQLHandler(BaseSQLHandler):
    """
    SQL database handler for mysql.
    """
    db_name = 'MySQL'

    def _connect(self, settings_dict):
        import MySQLdb as mysqldb
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
            stdout.warn(e.message)
            raise ConnectionTimeout
        return conn

class PrimitiveMssqlHandler(BaseSQLHandler):
    """
    Uses the primitive mssql instead of `SQLServerHandler` when doing
    INSERT, UPDATE or DELETE operation.
    see ref: http://pymssql.org/en/stable/_mssql_examples.html
    """
    db_name = '_mssql'

    def _connect(self, settings_dict):
        import _mssql
        try:
            conn = _mssql.connect(
                server=settings_dict['HOST'],
                port=settings_dict['PORT'],
                user=settings_dict['USER'],
                password=settings_dict['PASSWORD'],
                database=settings_dict['DATABASE'],
                charset=settings_dict['CHARSET']
            )
            conn.query_timeout=settings.DB_CONN_TIMEOUT,
        # _mssql is not written based on the PEP-249, `exceptions` on _mssql see:
        # http://pymssql.org/en/stable/ref/_mssql.html#module-level-exceptions
        except _mssql.MssqlDatabaseException as e:
            stdout.warn(e.message)
            raise ConnectionTimeout
        return conn

    def _get_cursor(self):
        """
        Differs from other database driver, `_mssql` executes operations
        without cursor.
        """
        return None

    def exec_query(self, operation):
        # About more details on `execute_query`, see:
        # http://pymssql.org/en/stable/ref/_mssql.html#_mssql.MSSQLConnection.execute_query
        def _operator(cursor, operation, *args):
            result = self._conn.execute_query(operation)
            return result

        return self.execute(operation, _operator)

    def exec_commit(self, operation):
        # About more details on `execute_non_query`, see:
        # http://pymssql.org/en/stable/ref/_mssql.html#_mssql.MSSQLConnection.execute_non_query
        def _operator(cursor, operation, *args):
            self._conn.execute_non_query(operation)
            naffected = self.conn.rows_affected
            stdout.info("Operation completed with '{}' rows affected.".format(naffected))
            return naffected

        return self.execute(operation, _operator)
