# -*- coding: utf-8 -*-
import time
import copy

from pymongo import MongoClient, errors
from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
from moose.core.terminal import stdout
from moose.conf import settings

import logging
logger = logging.getLogger(__name__)

class MongoDBHandler(object):
    """
    Wrapper for library pymongo, see ref:
    https://api.mongodb.com/python/current/tutorial.html
    """

    coll_source = 'Source'
    coll_result = 'Result'

    def __init__(self, settings_dict):
        if not isinstance(settings_dict, dict):
            raise ImproperlyConfigured(
                "Argument `settings_dict` is the configure for mongodb drivers, "
                "which must be an instance of `dict`.")

        self.settings_dict = settings_dict
        self.displayed_mongo_url = self.__get_displayed_url(settings_dict)
        self._client = self.__connect()
        self._db_name = None
        self._db = None
        self._coll_name = None
        self._coll = None

    def __del__(self):
        self.close()

    def __connect(self):
        mongo_url = self.__get_mongo_url(self.settings_dict)
        logger.debug("Connecting to '%s'..." % self.displayed_mongo_url)
        conn_cnt = 0
        while conn_cnt < settings.DB_CONN_MAX_TIMES:
            try:
                # More details about `MongoClient` API, see:
                # https://api.mongodb.com/python/2.8/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient
                client = MongoClient(mongo_url)
                # the constructor returns immediately and launches the
                # connection process on background threads.
                # Checks if the server is available like this:
                client.admin.command('ismaster')
                logger.debug("Connection to MongoDB is established.")
                return client
            # If auto-reconnection will be performed, AutoReconnect will be raised.
            # Application code should handle this exception (recognizing that the
            # operation failed) and then continue to execute.
            except errors.AutoReconnect as e:
                conn_cnt += 1
                msg = (
                    "Connection to MongoDB is lost and an attempt to "
                    "auto-connect will be made ..."
                    )
                stdout.warn(msg)
                logger.warning(msg)

        logger.error("Unable to establish the connection to MongoDB.")
        raise ImproperlyConfigured("Unable to establish the connection to MongoDB.")


    def __get_mongo_url(self, settings_dict):
        try:
            return "mongodb://{USER}:{PASSWORD}@{HOST}:{PORT}".format(**settings_dict)
        except KeyError as e:
            logger.error("Key missing, check '{}' was set.".format(str(e)))
            raise ImproperlyConfigured("Key missing, check '{}' was set.".format(str(e)))

    def __get_displayed_url(self, settings_dict):
        if settings_dict.get('PASSWORD'):
            shadow_settings = copy.deepcopy(settings_dict)
            shadow_settings['PASSWORD'] ='***'
            return self.__get_mongo_url(shadow_settings)
        else:
            # we don't handle key missing errors here
            return '***'

    @property
    def db(self):
        if self._db != None:
            return self._db
        else:
            logger.error("Database is not specified, call `set_database()` first.")
            raise ImproperlyConfigured("Database is not specified, call `set_database()` first.")

    def set_database(self, db_name):
        logger.debug("Set database to '{}'".format(db_name))
        try:
            self._db = self._client[db_name]
            self._db_name = db_name
        except errors.InvalidName as e:
            logger.warning("Unknown database specified: '{}'".format(db_name))
            raise ImproperlyConfigured("Unknown database specified: '{}'".format(db_name))

    @property
    def coll(self):
        if self._coll != None:
            return self._coll
        else:
            logger.error("Collection is not specified, call `set_collection()` first.")
            raise ImproperlyConfigured("Collection is not specified, call `set_collection()` first.")

    def set_collection(self, coll_name):
        logger.debug("Set collection to '{}'".format(coll_name))
        if self._coll_name != coll_name:
            try:
                self._coll = self.db[coll_name]
                self._coll_name = coll_name
            except errors.InvalidName as e:
                logger.warning("Unknown collection specified: '{}'".format(coll_name))
                raise ImproperlyConfigured("Unknown collection specified: '{}'".format(coll_name))

    def execute(self, coll_name, operator):
        conn_cnt = 0
        while conn_cnt < settings.DB_CONN_MAX_TIMES:
            try:
                self.set_collection(coll_name)
                result = operator()
                return result
            except (errors.AutoReconnect, errors.ExecutionTimeout):
                conn_cnt += 1
                logger.warning(
                    "Failed to execute the operation, an attempt to "
                    "re-connect will be made."
                    )

        raise ImproperlyConfigured("MongoDB: Failed too many times to execute, aborted.")


    def fetch(self, coll_name, filter=None, *args, **kwargs):
        logger.debug("Fetching from collection [%s] of '%s'." % (coll_name, self._db_name))

        def _operator():
            documents = []
            for doc in self.coll.find(filter, *args, **kwargs):
                documents.append(doc)
            return documents

        return self.execute(coll_name, _operator)

    def fetch_source(self, filter=None, *args, **kwargs):
        return self.fetch(self.coll_source, filter, *args, **kwargs)

    def fetch_result(self, filter=None, *args, **kwargs):
        return self.fetch(self.coll_result, filter, *args, **kwargs)

    def insert(self, coll_name, documents, **kwargs):
        if isinstance(documents, dict):
            documents = [documents]

        logger.warning(
            "Insert {} documents to the collection '{}'".format(len(documents), coll_name))
        def _operator():
            return self.coll.insert_many(documents, **kwargs)

        return self.execute(coll_name, _operator)

    def update(self, coll_name, filter, document, **kwargs):
        logger.warning("Update collection '{}' matching the filter: '{}'".format(coll_name, filter))
        def _operator():
            return self.coll.update_many(
                filter,
                {'$set': document},
                **kwargs
                )

        return self.execute(coll_name, _operator)

    def close(self):
        try:
            self._client.close()
        except AttributeError as e:
            logger.warning("No connections found.")
        else:
            logger.debug("Connection to '{}' closed.".format(self.displayed_mongo_url))
