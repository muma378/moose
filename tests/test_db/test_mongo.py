# -*- coding: utf-8 -*-
import copy
import mock
import unittest

from pymongo import errors

from moose.connection.mongodb import MongoDBHandler
from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from .config import mongo_settings

class MongoDBHandlerTestCase(unittest.TestCase):

    def setUp(self):
        self.mongo_patcher = mock.patch("moose.connection.mongodb.MongoClient")
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_client = mock.Mock()
        self.mock_mongo.return_value = self.mock_client

    def tearDown(self):
        self.mongo_patcher.stop()

    def test_connect(self):
        mongo_handler = MongoDBHandler(mongo_settings)
        self.mock_client.admin.command.assert_called_with("ismaster")
        self.assertEqual(mongo_handler.client, self.mock_client)
        self.assertEqual(
            mongo_handler.displayed_mongo_url,
            "mongodb://<user>:****@<host>:<port>")

        self.mock_client.admin.command = mock.Mock(side_effect=errors.ConnectionFailure)
        with self.assertRaises(ConnectionTimeout):
            mongo_handler = MongoDBHandler(mongo_settings)

        corrupt_settings = copy.deepcopy(mongo_settings)
        corrupt_settings.pop("HOST")
        with self.assertRaises(ImproperlyConfigured):
            mongo_handler = MongoDBHandler(corrupt_settings)
