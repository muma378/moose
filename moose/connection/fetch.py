# -*- coding: utf-8 -*-
import logging

from moose.core.exceptions import ImproperlyConfigured
from . import query
from . import database

class BaseFetcher(object):
    """
    Class to fetch result from mongodb according to information given
    by class 'query'.

    `query_cls`
        Subclass of moose.core.connection.query, implements the method
    'query' to get result from a sql database.

    `context`
        Specify compoenents composing the fetcher, including:
        - sql_hander: Subclass of BaseSQLHandler to connect database;
        - sql_context: A dict to represent configs for the sql connections,
            meanwhile including tables' alias in the database;
        - mongo_handler: Subclass of MongoDBHandler to connect mongodb;
        - mongo_context: A dict to represent configs for mongo connections;
    """
    # TODO: using parameters sql_handler and mongo_handler makes more sense?
    def __init__(self, query_cls, context):
        self.sql_hander = context['sql_hander'](context['sql_context'])
        sql_table_alias = context['sql_context']['TABLE_ALIAS']
        self.querier = query_cls(self.sql_hander, sql_table_alias)
        self.mongo = context['mongo_handler'](context['mongo_context'])

    def _fetch_source(self, project_id):
        self.mongo.set_database(project_id)
        records = []
        for record in self.mongo.fetch_source():
            records.append(record)
        return records

    def _fetch_result(self, project_id):
        self.mongo.set_database(project_id)
        records = []
        for record in self.mongo.fetch_result():
            records.append(record)
        return records

    def _indexing(self, records, key='_guid'):
        return {r[key]: r for r in records}

    def fetch(self, **context):
        project_id = context['project_id']

        # get sql queryset
        queryset = self.querier.query(**context)

        # get mongo result
        source_records = self._indexing(self._fetch_source(project_id))
        result_records = self._indexing(self._fetch_result(project_id))

        # match records in table source and result
        records = []
        for source_guid, result_guid in queryset:
            if result_records.get(str(result_guid)):
                records.append({
                    'source': source_records[str(source_guid)],
                    'result': result_records[str(result_guid)],
                    })
            else:
                logger.error("Unable to find match result record for guid: '%s'" % str(result_guid))
        return records
