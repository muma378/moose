# -*- coding: utf-8 -*-
import copy
import mock
import unittest

from pymongo import errors
from pymongo.mongo_client import MongoClient

from moose.connection.mongodb import MongoDBHandler
from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from moose.conf import settings
from .config import mongo_settings

class MongoDBHandlerTestCase(unittest.TestCase):

    def setUp(self):
        self.mongo_patcher = mock.patch("moose.connection.mongodb.MongoClient")
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_client = mock.MagicMock(spec=MongoClient, admin=mock.Mock())
        self.mock_mongo.return_value = self.mock_client

        self.mongo_handler = MongoDBHandler(mongo_settings)


    def tearDown(self):
        self.mongo_patcher.stop()

    def test_connect(self):
        mongo_handler = MongoDBHandler(mongo_settings)
        self.mock_client.admin.command.assert_called_with("ismaster")
        self.assertEqual(mongo_handler._client, self.mock_client)
        self.assertEqual(
            mongo_handler.displayed_mongo_url,
            "mongodb://<user>:***@<host>:<port>")

        self.mock_mongo.reset_mock()
        self.mock_client.admin.command = mock.Mock(side_effect=errors.AutoReconnect)
        with self.assertRaises(ImproperlyConfigured):
            mongo_handler = MongoDBHandler(mongo_settings)
        self.assertEqual(self.mock_mongo.call_count, settings.DB_CONN_MAX_TIMES)

        corrupt_settings = copy.deepcopy(mongo_settings)
        corrupt_settings.pop("HOST")
        with self.assertRaises(ImproperlyConfigured):
            mongo_handler = MongoDBHandler(corrupt_settings)

    def test_set_database(self):
        mongo_handler = MongoDBHandler(mongo_settings)

        # called with no setter
        with self.assertRaises(ImproperlyConfigured):
            mongo_handler.db

        def get_db_instance(name):
            if name == 'test':
                return 'test-db'
            else:
                raise errors.InvalidName
        self.mock_client.__getitem__ = mock.Mock(side_effect = get_db_instance)

        # called with invalid names
        with self.assertRaises(ImproperlyConfigured):
            mongo_handler.set_database('undefined')

        # called in correct process
        mongo_handler.set_database('test')
        self.mock_client.__getitem__.assert_called_with('test')
        self.assertEqual(mongo_handler._db_name, 'test')
        self.assertEqual(mongo_handler.db, 'test-db')

    @mock.patch.object(MongoDBHandler, "db")
    def test_set_collection(self, mock_db):
        mongo_handler = MongoDBHandler(mongo_settings)

        # called with no setter
        with self.assertRaises(ImproperlyConfigured):
            mongo_handler.coll

        def get_coll_instance(name):
            if name == 'test':
                return 'test-coll'
            else:
                raise errors.InvalidName
        mongo_handler.db.__getitem__ = mock.Mock(side_effect = get_coll_instance)

        # called with invalid names
        with self.assertRaises(ImproperlyConfigured):
            mongo_handler.set_collection('undefined')

        # called in correct process
        mongo_handler.set_collection('test')
        mongo_handler.db.__getitem__.assert_called_with('test')
        self.assertEqual(mongo_handler._coll_name, 'test')
        self.assertEqual(mongo_handler.coll, 'test-coll')

    @mock.patch.object(MongoDBHandler, "set_collection")
    def test_execute(self, mock_set_coll):
        operator = mock.Mock(return_value='ok')
        self.assertEqual(self.mongo_handler.execute('test', operator), 'ok')
        mock_set_coll.assert_called_with('test')

        mock_set_coll.reset_mock()
        operator = mock.Mock(side_effect=errors.AutoReconnect)
        with self.assertRaises(ImproperlyConfigured):
            self.mongo_handler.execute('test', operator)
        self.assertEqual(mock_set_coll.call_count, settings.DB_CONN_MAX_TIMES)

        mock_set_coll.reset_mock()
        operator = mock.Mock(side_effect=errors.ExecutionTimeout("timeout"))
        with self.assertRaises(ImproperlyConfigured):
            self.mongo_handler.execute('test', operator)
        self.assertEqual(mock_set_coll.call_count, settings.DB_CONN_MAX_TIMES)


    @mock.patch.object(MongoDBHandler, "coll")
    @mock.patch.object(MongoDBHandler, "set_collection")
    def test_fetch(self, mock_set_coll, mock_coll):
        filter = {"key": 1}
        document = [{"key": 1, "value": "test"}]

        mock_coll.find = mock.Mock(return_value=document)

        # call with no filter
        self.assertEqual(self.mongo_handler.fetch('test'), document)
        mock_set_coll.assert_called_with('test')
        mock_coll.find.assert_called_with(None)

        # call with a filter
        mock_set_coll.reset_mock()
        mock_coll.reset_mock()
        self.assertEqual(self.mongo_handler.fetch('test', filter), document)
        mock_set_coll.assert_called_with('test')
        mock_coll.find.assert_called_with(filter)

        # call the defered methods
        self.assertEqual(self.mongo_handler.fetch_source(filter), document)
        mock_set_coll.assert_called_with('Source')
        self.assertEqual(self.mongo_handler.fetch_result(filter), document)
        mock_set_coll.assert_called_with('Result')

        mock_coll.find = mock.Mock(side_effect=errors.AutoReconnect)
        with self.assertRaises(ImproperlyConfigured):
            self.mongo_handler.fetch('test', filter)

    @mock.patch.object(MongoDBHandler, "coll")
    @mock.patch.object(MongoDBHandler, "set_collection")
    def test_insert(self, mock_set_coll, mock_coll):
        document = [{"key": 1, "value": "test"}]

        mock_coll.insert_many = mock.Mock(return_value=document)

        # call with a single document
        self.assertEqual(self.mongo_handler.insert('test', document[0]), document)
        mock_set_coll.assert_called_with('test')
        mock_coll.insert_many.assert_called_with(document)

        # call with mutiple documents
        mock_set_coll.reset_mock()
        mock_coll.reset_mock()
        self.assertEqual(self.mongo_handler.insert('test', document), document)
        mock_set_coll.assert_called_with('test')
        mock_coll.insert_many.assert_called_with(document)

        mock_coll.insert_many = mock.Mock(side_effect=errors.AutoReconnect)
        with self.assertRaises(ImproperlyConfigured):
            self.mongo_handler.insert('test', document)

    @mock.patch.object(MongoDBHandler, "coll")
    @mock.patch.object(MongoDBHandler, "set_collection")
    def test_update(self, mock_set_coll, mock_coll):
        filter = {"key": 1}
        document = {"key": 1, "value": "test"}

        mock_coll.update_many = mock.Mock(return_value=document)

        # calls with no filter
        with self.assertRaises(TypeError):
            self.assertEqual(self.mongo_handler.update('test', document), document)

        # calls with filter
        mock_set_coll.reset_mock()
        mock_coll.reset_mock()
        self.assertEqual(self.mongo_handler.update('test', filter, document), document)
        mock_set_coll.assert_called_with('test')
        mock_coll.update_many.assert_called_with(filter, {'$set': document})

        mock_coll.update_many = mock.Mock(side_effect=errors.AutoReconnect)
        with self.assertRaises(ImproperlyConfigured):
            self.mongo_handler.update('test', filter, document)
