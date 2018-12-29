# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pymssql
import _mssql

from .sqlhandler import BaseSQLHandler

from moose.core.terminal import stdout
from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from moose.conf import settings

import logging
logger = logging.getLogger(__name__)


class SQLServerHandler(BaseSQLHandler):
    """
    SQL database handler for sql server.
    """

    db_name = 'SQLServer'

    def _connect(self, settings_dict):
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
            stdout.warn(str(e))
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


class PrimitiveMssqlHandler(BaseSQLHandler):

    """
    Uses the primitive mssql instead of `SQLServerHandler` when doing
    INSERT, UPDATE or DELETE operation.
    see ref: http://pymssql.org/en/stable/_mssql_examples.html
    """
    db_name = '_mssql'

    def _connect(self, settings_dict):
        try:
            conn = _mssql.connect(
                server=settings_dict['HOST'],
                port=settings_dict['PORT'],
                user=settings_dict['USER'],
                password=settings_dict['PASSWORD'],
                database=settings_dict['DATABASE'],
                charset=settings_dict['CHARSET']
            )
            conn.query_timeout = settings.DB_CONN_TIMEOUT
        # _mssql is not written based on the PEP-249, `exceptions` on _mssql see:
        # http://pymssql.org/en/stable/ref/_mssql.html#module-level-exceptions
        except _mssql.MssqlDatabaseException as e:
            stdout.warn(str(e))
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
            naffected = self._conn.rows_affected
            stdout.info("Operation completed with '{}' rows affected.".format(naffected))
            return naffected

        return self.execute(operation, _operator)
