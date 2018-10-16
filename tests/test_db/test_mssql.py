# -*- coding: utf-8 -*-
import unittest

import pymssql
import _mssql

from moose.connection import mssql
from moose.core.exceptions import ImproperlyConfigured
from moose.conf import settings

from ._sqlhandler import SQLHandlerBaseTest
from .config import sql_settings as mssql_settings


class SQLServerHandlerTestCase(SQLHandlerBaseTest, unittest.TestCase):

    connect_patch_module = "moose.connection.mssql.pymssql.connect"
    settings_dict = mssql_settings

    def init_sqlhandler(self, settings_dict=mssql_settings):
        return mssql.SQLServerHandler(settings_dict)

    def test_connect_timeout(self):
        # test if try to reconnect
        self.mock_connect.side_effect = pymssql.InternalError
        with self.assertRaises(ImproperlyConfigured):
            self.init_sqlhandler()
        self.assertEqual(self.mock_connect.call_count, settings.DB_CONN_MAX_TIMES)
        self.mock_connect.assert_called_with(
            host='<host>', port='<port>', user='<user>',
            password='<password>', database='<database>',
            charset='UTF-8', timeout=settings.DB_CONN_TIMEOUT
            )


class PrimitiveMssqlHandlerTestCase(SQLHandlerBaseTest, unittest.TestCase):
    """
    Note that there was no `cursor` in `_mssql`, therefore the unittest
    for `PrimitiveMssqlHandler` is mainly to test the attribute `_conn`,
    and assumes the cursor was return as None.
    """

    connect_patch_module = "moose.connection.mssql._mssql.connect"
    settings_dict = mssql_settings

    def setUp(self):
        super(PrimitiveMssqlHandlerTestCase, self).setUp()
        self.mock_cursor = None

    def init_sqlhandler(self, settings_dict=mssql_settings):
        return mssql.PrimitiveMssqlHandler(settings_dict)

    def test_connect_timeout(self):
        # test if the driver was try to reconnect
        self.mock_connect.side_effect = _mssql.MssqlDatabaseException("test")
        with self.assertRaises(ImproperlyConfigured):
            self.init_sqlhandler()
        self.assertEqual(self.mock_connect.call_count, settings.DB_CONN_MAX_TIMES)
        self.mock_connect.assert_called_with(
            server='<host>', port='<port>', user='<user>',
            password='<password>', database='<database>',
            charset='UTF-8'
            )

    def test_connect(self):
        sql_handler = self.init_sqlhandler()
        self.assertEqual(self.mock_connect.call_count, 1)
        self.assertIs(sql_handler._conn, self.mock_conn)
        self.assertEqual(self.mock_conn.query_timeout, settings.DB_CONN_TIMEOUT)

    def test_cursor(self):
        sql_handler = self.init_sqlhandler()
        # note that no cursor existed in `_mssql`
        self.assertEqual(sql_handler._get_cursor(), None)

    def test_query(self):
        sql_handler = self.init_sqlhandler()

        self.mock_conn.execute_query.return_value = "1"
        self.assertEqual(sql_handler.exec_query("operation"), "1")
        self.mock_conn.execute_query.assert_called_once_with("operation")

    def test_commit(self):
        sql_handler = self.init_sqlhandler()

        self.mock_conn.rows_affected = 1
        self.assertEqual(sql_handler.exec_commit("operation"), 1)
        self.mock_conn.execute_non_query.assert_called_once_with("operation")

    def test_exec_many(self):
        # not implemented in `PrimitiveMssqlHandler`
        pass
