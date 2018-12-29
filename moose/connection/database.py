# -*- coding: utf-8 -*-
# database.py - provides uniform interfaces to query or modify the database
# authors: Liu Size, Xiao Yang<xiaoyang0117@gmail.com>
# date: 2016.01.28

import sys
import time
import random

from pymongo import MongoClient, errors
from moose.core.exceptions import ConnectionTimeout, ImproperlyConfigured

import logging
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
        except AttributeError as e:
            logger.debug("No connections established.")
        else:
            logger.debug("Connection to %s closed." % self.database_name)

    # not guaranteed, try to connect in 3 times
    def __connect(self):
        conn_cnt = 0
        while conn_cnt < RETRY_TIME:
            try:
                conn = self.get_connection(self.settings_dict)    # implemented by subclasses
                logger.debug("Connection established.")
                return conn
            except ConnectionTimeout as e:    # TODO:add a specified exception
                conn_cnt += 1
                logger.warning(
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
        except AttributeError as e:
            logger.warning("Connection closed already.")

    # guarantee to return a reliable connection
    def connect(self):
        while not self.conn:
            self.conn = self.__connect()
            if not self.conn:
                interval = random.randint(0, MAX_INTERVAL)
                logger.warning("Will try to connect the database in next %ss." % interval)
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
            return None
        naffected =  self.cursor.rowcount
        logger.info("Commitment executed successfully with '{}' rows affected.".format(naffected))
        return naffected

    def exec_many(self, sql, arg):
        raise NotImplementedError("Database you use not provided method 'exec_many()' yet.")


class SQLServerHandler(BaseSQLHandler):
    """
    Database instance to query and modify data in the sqlserver
    """
    database_name = 'SQLServer'

    def get_connection(self, settings_dict):
        import pymssql

        logger.debug(
                "Trying to connect to SQLServer servered on '%s:%s'..." % (settings_dict['HOST'], settings_dict['PORT']))
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
            logger.error(str(e))
            raise ImproperlyConfigured("Failed to connect to SQL database '%s'." % settings_dict['HOST'])
        except KeyError as e:
            logger.error(
                "Fields missing, please check {} was in settings.".format(str(e)))
            raise ImproperlyConfigured("Fields missing: {}".format(str(e)))
        return conn

    def exec_many(self, sql_commit, rows):
        if not sql_commit:
            logger.error("Invalid SQL statement for no content, aborted.")
            return

        if not self.conn:
            self.conn = self.connect()

        self.cursor = self.conn.cursor()

        # see ref: http://pymssql.org/en/stable/pymssql_examples.html
        try:
            logger.info("Executing the statement:\n\t'%s'." % sql_commit)
            self.cursor.executemany(sql_commit, rows)
            self.conn.commit()
        except Exception as e:
            logger.error(e)
            return

        logger.info('Commitment executed successfully.')


class MySQLHandler(BaseSQLHandler):
    """
    An alternative database for independent environment
    """
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
            logger.error(str(e))
            raise ImproperlyConfigured
        except KeyError as e:
            logger.error(
                "Fields missing, please check {} was in settings.".format(str(e)))
            raise ImproperlyConfigured("Fields missing: {}".format(str(e)))
        return conn

class PrimitiveMssqlHandler(BaseSQLHandler):
    """
    Uses the primitive mssql instead of BaseSQLHandler when doing insert
    see ref: http://pymssql.org/en/stable/_mssql_examples.html
    """
    database_name = '_mssql'

    def get_connection(self, settings_dict):
        import _mssql

        logger.debug(
                "Trying to connect to SQLServer servered on '%s:%s'..." % (settings_dict['HOST'], settings_dict['PORT']))
        conn = None
        try:
            conn = _mssql.connect(
                server=settings_dict['HOST'],
                port=settings_dict['PORT'],
                user=settings_dict['USER'],
                password=settings_dict['PASSWORD'],
                database=settings_dict['DATABASE'],
                charset=settings_dict['CHARSET']
            )
        except _mssql.MssqlDatabaseException as e:
            logger.error(str(e))
            raise ImproperlyConfigured("Failed to connect to SQL database '%s'." % settings_dict['HOST'])
        except KeyError as e:
            logger.error(
                "Fields missing, please check {} was in settings.".format(str(e)))
            raise ImproperlyConfigured("Fields missing: {}".format(str(e)))
        return conn


    def exec_commit(self, sql_commit):
        import _mssql
        if not sql_commit:
            logger.error("Invalid SQL statement for no content, aborted.")
            return False

        if not self.conn:
            self.conn = self.connect()

        try:
            logger.info("Executing the statement:\n\t'%s'." % sql_commit)
            self.conn.execute_non_query(sql_commit)
        except _mssql.MssqlDatabaseException as e:
            if e.number == 2714 and e.severity == 16:
                # table already existed, so quieten the error
                pass
            else:
                raise # re-raise real error

        logger.info("Commitment executed successfully.")
        return

    def exec_many(self, sql_commit, rows):
        import _mssql
        if not sql_commit:
            logger.error("Invalid SQL statement for no content, aborted.")
            return False

        if not self.conn:
            self.conn = self.connect()

        try:
            logger.info("Executing the statement:\n\t'%s' with %d rows." % (sql_commit, len(rows)))
            insert_op, _, value_op = sql_commit.rpartition('values')
            insert_op += 'values'
            for row in rows:
                insert_op += value_op % row + ','
            insert_op = insert_op[:-1]
            self.conn.execute_non_query(insert_op)
        except _mssql.MssqlDatabaseException as e:
            if e.number == 2714 and e.severity == 16:
                # table already existed, so quieten the error
                pass
            else:
                raise # re-raise real error

        logger.info("Commitment executed successfully.")
        return


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

    def fetch(self, coll, cond={}):
        try:
            logger.debug("Fetch data from collection [%s] of '%s'." % (coll, self.db_name))
            for item in self.db[coll].find(cond):
                yield item
        except errors.ServerSelectionTimeoutError as e:
            logger.warning("Timeout to fetch data from [%s]." % coll)
            raise ConnectionTimeout
        except errors.AutoReconnect as e:
            count = 1
            logger.warning("Failed, retry to connect to '%s' for %d time(s)." % (self.db_name, count))
            while count <= RETRY_TIME:
                try:
                    time.sleep(5)
                    for item in self.db[coll].find(cond):
                        yield item
                    break
                except errors.AutoReconnect as e:
                    count += 1
                    logger.warning("Retry to fetch data from '%s' for %d time(s)." % (self.db_name, count))

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
        except AttributeError as e:
            logger.warning("No connections found.")
        else:
            logger.debug("Connection to %s closed." % self.host)
