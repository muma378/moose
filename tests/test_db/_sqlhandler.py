# -*- coding: utf-8 -*-
import copy
import mock

from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from moose.conf import settings


class SQLHandlerBaseTest(object):

    settings_dict = None
    connect_patch_module = ""

    def setUp(self):
        self.time_patcher = mock.patch("moose.connection.sqlhandler.time")
        self.mock_time = self.time_patcher.start()
        self.mock_time.sleep.return_value = 1

        self.mock_conn   = mock.Mock()
        self.mock_cursor = mock.MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

        self.connect_patcher = mock.patch(self.connect_patch_module)
        self.mock_connect = self.connect_patcher.start()
        self.mock_connect.return_value = self.mock_conn

    def tearDown(self):
        self.time_patcher.stop()
        self.connect_patcher.stop()

    def init_sqlhandler(self, settings_dict=None):
        raise NotImplementedError

    def test_field_missing(self):
        corrupt_settings = copy.deepcopy(self.settings_dict)
        corrupt_settings.pop('HOST')
        with self.assertRaises(ImproperlyConfigured):
            self.init_sqlhandler(corrupt_settings)
        self.assertEqual(self.mock_connect.call_count, 0)

    def test_connect_timeout(self):
        # test if try to reconnect
        raise NotImplementedError

    def test_connect(self):
        sql_handler = self.init_sqlhandler()
        self.assertEqual(self.mock_connect.call_count, 1)
        self.assertIs(sql_handler._conn, self.mock_conn)

    def test_execute(self):
        sql_handler = self.init_sqlhandler()

        mock_operator = mock.Mock()
        with self.assertRaises(SuspiciousOperation):
            sql_handler.execute(None, mock_operator)

        sql_handler.execute("operation", mock_operator, "param1", "param2")
        mock_operator.assert_called_once_with(self.mock_cursor, "operation", "param1", "param2")

        mock_operator = mock.Mock(side_effect=ValueError)
        self.assertEqual(sql_handler.execute("operation", mock_operator), None)

    def test_query(self):
        sql_handler = self.init_sqlhandler()

        sql_handler.exec_query("operation")
        self.mock_cursor.execute.assert_called_once_with("operation")
        self.mock_cursor.fetchall.assert_called_once_with()

        self.mock_cursor.reset_mock()
        sql_handler.exec_query("$table_source")
        self.mock_cursor.execute.assert_called_once_with("[10.0.0.201].CrowdDB.dbo.DataSource")

    def test_commit(self):
        sql_handler = self.init_sqlhandler()

        self.mock_cursor.rowcount = 1
        self.assertEqual(sql_handler.exec_commit("operation"), 1)
        self.mock_cursor.execute.assert_called_once_with("operation")
        self.mock_conn.commit.assert_called_once_with()

    def test_exec_many(self):
        sql_handler = self.init_sqlhandler()

        with self.assertRaises(TypeError):
            sql_handler.exec_many("operation", "too", "many", "params")

        self.mock_cursor.rowcount = 3
        self.assertEqual(sql_handler.exec_many("operation", ("param1", "param2", "param3")), 3)
        self.mock_cursor.executemany.assert_called_once_with("operation", ("param1", "param2", "param3"))
        self.mock_conn.commit.assert_called_once_with()


    def test_close(self):
        sql_handler = self.init_sqlhandler()

        sql_handler.close()
        self.mock_conn.close.assert_called_once_with()
        self.assertEqual(sql_handler._conn, None)
        self.assertEqual(sql_handler._cursor, None)

        sql_handler.close()
        # No additional methods called
        self.mock_conn.close.assert_called_once_with()
