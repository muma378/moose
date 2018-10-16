# -*- coding: utf-8 -*-
import unittest

import MySQLdb as mysqldb

from moose.connection import mysql
from moose.core.exceptions import ImproperlyConfigured
from moose.conf import settings

from ._sqlhandler import SQLHandlerBaseTest
from .config import sql_settings as mysql_settings


class MySQLHandlerTestCase(SQLHandlerBaseTest, unittest.TestCase):
    connect_patch_module = "moose.connection.mysql.mysqldb.connect"
    settings_dict = mysql_settings

    def init_sqlhandler(self, settings_dict=mysql_settings):
        return mysql.MySQLHandler(settings_dict)

    def test_connect_timeout(self):
        # test if try to reconnect
        self.mock_connect.side_effect = mysqldb.InternalError
        with self.assertRaises(ImproperlyConfigured):
            self.init_sqlhandler()
        self.assertEqual(self.mock_connect.call_count, settings.DB_CONN_MAX_TIMES)
        self.mock_connect.assert_called_with(
            host='<host>', port='<port>', user='<user>',
            passwd='<password>', db='<database>', charset='UTF-8',
            connect_timeout=settings.DB_CONN_TIMEOUT
            )

    def test_exec_many(self):
        # not implemented in `MySQLHandler`
        pass
