# -*- coding: utf-8 -*-
import time

from pymongo import MongoClient, errors
from moose.core.exceptions import ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured
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
        self.settings_dict = settings_dict
        self.host = settings_dict['HOST']
        self.displayed_mongo_url = self.__get_display_mongo_url(settings_dict)
        self.client = self.__connect()

    def __del__(self):
        self.close()

    def __connect(self):
        mongo_url = self.__get_mongo_url(self.settings_dict)
        logger.debug("Connectting to '%s'..." % self.displayed_mongo_url)
        client = MongoClient(mongo_url)
        try:
            # the constructor returns immediately and launches the
            # connection process on background threads.
            # Checks if the server is available like this:
            client.admin.command('ismaster')
        except errors.ConnectionFailure as e:
            logger.error("Time out to connect '%s'." % self.displayed_mongo_url)
            raise ConnectionTimeout
        else:
            logger.debug("Connection established for MongoDB.")
            return client

    def __get_mongo_url(self, settings_dict):
        try:
            return "mongodb://{USER}:{PASSWORD}@{HOST}:{PORT}".format(**settings_dict)
        except KeyError as e:
            logger.error(
                "Please check if field '%s' was provided." % e)
            raise ImproperlyConfigured

    def __get_display_mongo_url(self, settings_dict):
        try:
            return "mongodb://{USER}:****@{HOST}:{PORT}".format(**settings_dict)
        except KeyError as e:
            logger.error("Please check if field '%s' was provided." % e)
            raise ImproperlyConfigured

    def set_database(self, db_name):
        self.db_name = db_name
        self.db = self.client[db_name]

    def fetch(self, coll, cond={}):
        try:
            logger.debug("Fetch data from collection [%s] of '%s'." % (coll, self.db_name))
            for item in self.db[coll].find(cond):
                yield item
        except errors.ServerSelectionTimeoutError as e:
            logger.warn("Timeout to fetch data from [%s]." % coll)
            raise ConnectionTimeout
        except errors.AutoReconnect as e:
            count = 1
            logger.warn("Failed, retry to connect to '%s' for %d time(s)." % (self.db_name, counter))
            while count <= settings.DB_CONN_MAX_TIMES:
                try:
                    time.sleep(5)
                    for item in self.db[coll].find(cond):
                        yield item
                    break
                except errors.AutoReconnect as e:
                    count += 1
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
        self.db[coll].update(
                            cond,
                            {'$set': document},
                            upsert=False
                            )

    def delete(self, coll, cond):
        self.db[coll].delete_one(cond)

    def close(self):
        try:
            self.client.close()
        except AttributeError,e:
            logger.warn("No connections found.")
        else:
            logger.debug("Connection to %s closed." % self.host)
