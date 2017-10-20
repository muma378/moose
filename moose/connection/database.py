# -*- coding: utf-8 -*-
# database.py - provides uniform interfaces to query or modify the database
# authors: Liu Size, Xiao Yang<xiaoyang0117@gmail.com>
# date: 2016.01.28

import sys
import time
import random
import logging

from pymongo import MongoClient, errors
from moose.core.exceptions import ConnectionTimeout, ImproperlyConfigured

logger = logging.getLogger(__name__)

MAX_INTERVAL = 500
RETRY_TIME = 3

class BaseSQLHandler(object):
    """
    Interface class for all SQL database opreations.
    """
    database_name = None

    def __init__(self, settings_dict):
        self.settings_dict = settings_dict
        self.host = settings_dict['HOST']
        self.conn = self.__connect()

    def __del__(self):
        try:
            self.conn.close()
        except AttributeError,e:
            logger.debug("No connections established.")
        else:
            logger.debug("Connection to %s closed." % self.database_name)

    # not guaranteed, try to connect in 3 times
    def __connect(self):
        conn_cnt = 0
        while conn_cnt < RETRY_TIME:
            try:
                conn = self.get_connection(self.settings_dict)	# implemented by subclasses
                logger.debug("Connection established.")
                return conn
            except ConnectionTimeout as e:	# TODO:add a specified exception
                conn_cnt += 1
                logger.warn(
                    "Connection failed for '%s',\n times to reconnect: %d." %\
                    (str(e), conn_cnt))

            logger.error("Unable to establish the connection, waiting for the next time.")
            return None

    def get_connection(self):
        raise NotImplementedError(
            "Subclass of 'BaseSQLHandler' must implement method get_connection().")

    def close(self):
        try:
            self.conn.close()
            self.conn = None
            self.cursor = None
        except AttributeError, e:
            logger.warn("Connection closed already.")

    # guarantee to return a reliable connection
    def connect(self):
        while not self.conn:
            self.conn = self.__connect()
            if not self.conn:
                interval = random.randint(0, MAX_INTERVAL)
                logger.warn("Will try to connect the database in next %ss." % interval)
                time.sleep(interval)
            return self.conn

    def exec_query(self, sql_query):
        if not sql_query:
            logger.error("Invalid SQL statement for no content, aborted.")
            return

        if not self.conn:
            self.conn = self.connect()

        # Get the cursor
        self.cursor = self.conn.cursor()

        try:
            logger.info("Executing the statement:\n\t'%s'" % sql_query)
            self.cursor.execute(sql_query)
            result = self.cursor.fetchall()
        except Exception as e:
            logger.error(e)
            return

        logger.info("Quering executed successfully.")
        return result

    # to add, delete and update
    def exec_commit(self, sql_commit):
        if not sql_commit:
            logger.error("Invalid SQL statement for no content, aborted.")
            return

        if not self.conn:
            self.conn = self.connect()

        self.cursor = self.conn.cursor()

        try:
            logger.info("Executing the statement:\n\t'%s'." % sql_commit)
            self.cursor.execute(sql_commit)
            self.conn.commit()
        except Exception as e:
            logger.error(e)
            return

        logger.info('Commitment executed successfully.')

    #TODO: execute many at one time
    #self.cursor.executemany()
    def exec_many(self, sql, arg):
        raise NotImplementedError

    def retrieve(self, *args, **kwargs):
        pass

class SQLServerHandler(BaseSQLHandler):
    """an instance to query and modify data in the sqlserver"""
    database_name = 'SQLServer'

    def get_connection(self, settings_dict):
        import pymssql

        logger.debug(
                "Trying to connect to SQLServer servered on '%s:%s'..." % (settings_dict['HOST'], settings_dict['HOST']))
        conn = None
        try:
            conn = pymssql.connect(
                host=settings_dict['HOST'],
                port=settings_dict['PORT'],
                user=settings_dict['USER'],
                password=settings_dict['PASSWORD'],
                database=settings_dict['DATABASE'],
                charset=settings_dict['CHARSET']
            )
        except (pymssql.InterfaceError, pymssql.OperationalError) as e:
            logger.error(e.message)
            raise ImproperlyConfigured
        except KeyError as e:
            logger.error(
                "Fields missing, please check %s was in settings." % e.message)
            raise ImproperlyConfigured("Fields missing: %s" % e.message)
        return conn


class MySQLHandler(BaseSQLHandler):
    """an alternative database for independent environment"""
    database_name = 'MySQL'

    def get_connection(self, settings_dict):
        import MySQLdb as mysqldb

        logger.debug(
            "Trying to connect to MySQL servered on '%s:%s'..." % (settings_dict['HOST'], settings_dict['PORT']))
        conn = None
        try:
            conn = mysqldb.connect(
                host=settings_dict['HOST'],
                port=settings_dict['PORT'],
                user=settings_dict['USER'],
                passwd=settings_dict['PASSWORD'],
                db=settings_dict['DATABASE'],
                charset=settings_dict['CHARSET']
                )
        except mysqldb.Error as e:
            logger.error(e.message)
            raise ImproperlyConfigured
        except KeyError as e:
            logger.error(
                "Fields missing, please check %s was in settings." % e.message)
            raise ImproperlyConfigured("Fields missing: %s" % e.message)
        return conn


class MongoDBHandler(object):
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
            client.address
        except errors.ServerSelectionTimeoutError as e:
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

    def fetch(self, table, cond={}):
        try:
            logger.debug("Fetch data from table [%s] of '%s'." % (table, self.db_name))
            for item in getattr(self.db, table).find(cond):
                yield item
        except errors.ServerSelectionTimeoutError as e:
            logger.warn("Timeout to fetch data from [%s]." % table)
            raise ConnectionTimeout
        except errors.AutoReconnect as e:
            count = 1
            while count <= RETRY_TIME:
                try:
                    time.sleep(5)
                    for item in getattr(self.db, table).find(cond):
                        yield item
                    break
                except errors.AutoReconnect as e:
                    count += 1
                    logger.warn("Retry to fetch data from '%s' for %d time(s)." % (self.db_name, count))

    def fetch_source(self, cond={}):
        for item in self.fetch('Source', cond):
            yield item

    def fetch_result(self, cond={}):
        for item in self.fetch('Result', cond):
            yield item

    def close(self):
        try:
            self.client.close()
        except AttributeError,e:
            logger.warn("No connections found.")
        else:
            logger.debug("Connection to %s closed." % self.host)
