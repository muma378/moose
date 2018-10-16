# -*- coding: utf-8 -*-
import logging

from moose.core.exceptions import ImproperlyConfigured
from moose.utils.module_loading import import_string
from moose.utils import six
from . import query, database

import logging
logger = logging.getLogger(__name__)

class BaseFetcher(object):
    """
    Class to fetch result from mongodb according to information given
    by class 'query'.

    `query_cls`
        Subclass of moose.core.connection.query, implements the method
    'query' to get result from a sql database.

    `context`
        Specify compoenents composing the fetcher, including:
        - sql_handler: Subclass of BaseSQLHandler to connect database;
        - sql_context: A dict to represent configs for the sql connections,
            meanwhile including tables' alias in the database;
        - mongo_handler: Subclass of MongoDBHandler to connect mongodb;
        - mongo_context: A dict to represent configs for mongo connections;
    """
    def __init__(self, query_cls, context):
        self.sql_handler = self.__load_or_import(context['sql_handler'], \
                                database.BaseSQLHandler, context['sql_context'])
        sql_table_alias = context['sql_context']['TABLE_ALIAS']
        if not issubclass(query_cls, query.BaseGuidQuery):
            raise ImproperlyConfigured(\
                "Query handler must be a subclass of query.BaseGuidQuery.")
        self.querier = query_cls(self.sql_handler, sql_table_alias)
        self.mongodb = self.__load_or_import(context['mongo_handler'], \
                            database.MongoDBHandler, context['mongo_context'])

    def __load_or_import(self, handler_cls, base_cls, context):
        if isinstance(handler_cls, six.string_types):
            handler_cls = import_string(handler_cls)
        if issubclass(handler_cls, base_cls):
            return handler_cls(context)
        else:
            raise ImproperlyConfigured(\
                "Database handlers must be a subclass of {}.".format(base_cls))

    def _fetch_source(self, project_id):
        self.mongodb.set_database(project_id)
        records = []
        for record in self.mongodb.fetch_source():
            records.append(record)
        return records

    def _fetch_result(self, project_id):
        self.mongodb.set_database(project_id)
        records = []
        for record in self.mongodb.fetch_result():
            records.append(record)
        return records

    def _indexing(self, records, key='_guid'):
        return {r[key]: r for r in records}

    def fetch(self, **context):
        project_id = str(context['project_id'])

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

class SourceFetcher(BaseFetcher):

    def fetch(self, **context):
        project_id = str(context['project_id'])
        # get sql queryset
        queryset = self.querier.query(**context)
        # get mongo result
        source_records = self._indexing(self._fetch_source(project_id))

        records = []
        for source_guid, _ in queryset:
            if source_records.get(str(source_guid)):
                records.append({
                    'source': source_records[str(source_guid)],
                    'result': {},
                    })
            else:
                logger.error("Unable to find match source record for guid: '%s'" % str(result_guid))
        return records


class ResultFetcher(BaseFetcher):

    def fetch(self, **context):
        project_id = str(context['project_id'])
        # get sql queryset
        queryset = self.querier.query(**context)
        # get mongo result
        result_records = self._indexing(self._fetch_result(project_id))

        records = []
        for _, result_guid in queryset:
            if result_records.get(str(result_guid)):
                records.append({
                    'source': {},
                    'result': result_records[str(result_guid)],
                    })
            else:
                logger.error("Unable to find match source record for guid: '%s'" % str(result_guid))
        return records


class AcquisitionFetcher(BaseFetcher):

    def fetch(self, **context):
        project_id = str(context['project_id'])
        # get mongo result
        result_records = self._indexing(self._fetch_result(project_id))

        records = []
        for _, result in result_records.items():
            records.append({
                'source': {},
                'result': result,
                })
        return records
