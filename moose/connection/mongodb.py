# -*- coding: utf-8 -*-
import time

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

    def __del__(self):
        self.close()

    def __connect(self):
        mongo_url = self.__get_mongo_url(self.settings_dict)
        logger.debug("Connecting to '%s'..." % self.displayed_mongo_url)
        while
        try:
            # More details about `MongoClient` API, see:
            # https://api.mongodb.com/python/2.8/api/pymongo/mongo_client.html#pymongo.mongo_client.MongoClient
            client = MongoClient(mongo_url)
            # the constructor returns immediately and launches the
            # connection process on background threads.
            # Checks if the server is available like this:
            client.admin.command('ismaster')
        except errors.ConnectionFailure as e:
            logger.error("Timeout to connect to '%s'." % self.displayed_mongo_url)
            raise ImproperlyConfigured()
        # If auto-reconnection will be performed, AutoReconnect will be raised.
        # Application code should handle this exception (recognizing that the
        # operation failed) and then continue to execute.
        except errors.AutoReconnect as e:
            pass

        else:
            logger.debug("Connection established for MongoDB.")
            return client

    def __get_mongo_url(self, settings_dict):
        try:
            return "mongodb://{USER}:{PASSWORD}@{HOST}:{PORT}".format(**settings_dict)
        except KeyError as e:
            logger.error("Key missing, check '{}' was set.".format(e.message))
            raise ImproperlyConfigured("Key missing, check '{}' was set.".format(e.message))

    def __get_displayed_url(self, settings_dict):
        try:
            return "mongodb://{USER}:****@{HOST}:{PORT}".format(**settings_dict)
        except KeyError as e:
            logger.error("Key missing, check '{}' was set.".format(e.message))
            raise ImproperlyConfigured("Key missing, check '{}' was set.".format(e.message))

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
            logger.warn("Unknown database specified: '{}'".format(db_name))
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
        if self._coll_name == coll_name:
            return self._coll
        else:
            try:
                self._coll = self.db[coll_name]
                self._coll_name = coll_name
            except errors.InvalidName as e:
                logger.warn("Unknown collection specified: '{}'".format(coll_name))
                raise ImproperlyConfigured("Unknown collection specified: '{}'".format(coll_name))

    def execute(self, coll, operator, filter, *args):

        self.set_collection(coll)
        operator(filter)


    def fetch(self, coll, cond={}):
        try:
            self.set_collection(coll)
            logger.debug("Fetch data from collection [%s] of '%s'." % (coll, self.db_name))
            for item in self.coll.find(cond):
                yield item
        except errors.ExecutionTimeout as e:
            conn_cnt = 1
            logger.warn("Failed, retry to connect to '%s' for %d time(s)." % (self.db_name, counter))
            while conn_cnt <= settings.DB_CONN_MAX_TIMES:
                try:
                    time.sleep(5)
                    for item in self.coll.find(cond):
                        yield item
                    break
                except errors.ExecutionTimeout as e:
                    conn_cnt += 1
                    logger.warn("Retry to fetch data from '%s' for %d time(s)." % (self.db_name, count))


    def fetch_source(self, cond={}):
        for item in self.fetch(self.coll_source, cond):
            yield item

    def fetch_result(self, cond={}):
        for item in self.fetch(self.coll_result, cond):
            yield item

    def insert(self, coll, document):
        self.db[coll].insert(document)

    def update_result(self, cond, document):
        self.update(self.coll_result, cond, document)

    def update(self, coll, cond, document):
        logger.warn("Updating collection '{}' with '{}'".format(coll, cond))
        self.db[coll].update(
                            cond,
                            {'$set': document},
                            upsert=False
                            )

    def delete(self, coll, cond):
        self.db[coll].delete_one(cond)

    def close(self):
        try:
            self._client.close()
        except AttributeError,e:
            logger.warn("No connections found.")
        else:
            logger.debug("Connection to %s closed." % self.host)
