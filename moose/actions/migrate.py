# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import math
import time
import copy
import pprint
import pickle
import hashlib
from datetime import datetime

from moose.connection import query, fetch
from moose.utils._os import makedirs, makeparents, npath
from moose.utils.module_loading import import_string
from moose.utils.serialize import load_xlsx
from moose.conf import settings

from .base import IllegalAction, InvalidConfig, QueryError
from .base import SimpleAction

import logging
logger = logging.getLogger(__name__)


class BaseMigrate(SimpleAction):
    """
    Action to migrate tasks of acquisition to annotation
    """

    project_query_class = query.ProjectInfoQuery
    migrate_operate_class = query.AcqToMarkByUserguid
    # Query context to be passed in `fetcher_class`, find more details in
    # `settings.QUERY_CONTEXT`
    query_context   = {}
    insert_context  = {}
    # Whether the fetched result to be kept and how long (in hour)
    use_cache       = True
    cache_dirname   = settings.DATACACHE_DIRNAME
    cache_lifetime  = settings.DATACACHE_LIFETIME
    create_time_format = '%Y-%m-%d %H:%M:%S'


    def parse(self, kwargs):
        # Gets config from the kwargs
        config = self.get_config(kwargs)

        if self.project_query_class:
            self.project_querier = self.project_query_class.create_from_context(
                                    self.query_context)

        if self.migrate_operate_class:
            self.migrate_operator = self.migrate_operate_class.create_from_context(
                                    self.insert_context
            )

        # Sets base environment
        environment = {
            'workbook': config.common['migrate'],
        }

        # Sets custom environment
        self.set_environment(environment, config, kwargs)
        return environment

    def schedule(self, env):
        """
        Generates the context to execute in the following steps.
        """
        for i, context in self.get_querypairs(env):
            if not self.is_valid(context):
                logger.error("Invalid arguments context:\n '{}''".format(pprint.format(context)))
                continue
            yield context

    def is_valid(self, context):
        """
        Check if the context is correct.
        """
        return True

    def get_querypairs(self, env):
        """
        An iterator to generate pairs of queryargs
        """
        raise NotImplementedError("subclasses of BaseMigrate must provide a `get_querypairs()`")

    def _get_create_time(self):
        return datetime.now().strftime(self.create_time_format)

    def query(self, **kwargs):
        return {}

    def insert(self, **kwargs):
        self.migrate_operator.execute(**kwargs)

    def execute(self, context):
        queryset = self.query(context)


class SimpleMigrate(BaseMigrate):

    userguid_query_class = query.UserGuidInProjectQuery
    query_context   = settings.QUERY_CONTEXT
    insert_context  = settings.INSERT_CONTEXT

    sheet_title = u'Sheet1'
    start = 1
    end = None


    def set_environment(self, env, config, kwargs):
        self.workbook = load_xlsx(env['workbook'])[self.sheet_title][self.start:self.end]

        self.userguid_querier = self.userguid_query_class.create_from_context(
                                self.query_context)

        env.update({
            'group_column': config.migrate['group_column'],
            'acq_task_column': config.migrate['acq_task_column'],
            'batch_name_column': config.migrate['batch_name_column']
        })


    def _get_key(self, context):
        return context['group_id']+'@'+context['acq_task_id']

    def get_querypairs(self, env):
        querypairs = []
        counter = 0
        for row in self.workbook:
            if row and any(row):
                context = {
                    'group_id': row[env['group_column']],
                    'acq_task_id': row[env['acq_task_column']],
                    'batch_name': row[env['batch_name_column']],
                    'row': row,
                }

                counter += 1
                yield counter, context

    def _get_username(self, group_id):
        # when group ids were 4 digits and less than 2000,
        # the username would be DGYYXXXX. For example:
        # G0100 => DGYY0100, G1100 => DGYY1100
        if group_id.startswith('G') and len(group_id) == 5\
            and int(group_id[1]) < 2:
            return 'DGYY' + group_id[1:]
        else:
            return group_id

    def get_hidden_username(self, group_id):
        raise NotImplementedError(
            "subclasses of BaseMigrate must provide a `get_hidden_username()` "
            "to solve IncorrectUsername error."
            )

    def get_user_guid(self, group_id, task_id):
        username = self._get_username(group_id)
        user_guid = self.userguid_querier.query(user_name=username, project_id=task_id)
        if not user_guid:
            # try with another possible username
            username = self.get_hidden_username(group_id)
            user_guid = self.userguid_querier.query(user_name=username, project_id=task_id)

            if not user_guid:
                logger.error("Unknown username found for group id [{}]@{}".format(group_id, task_id))
                raise QueryError("Unknown username found for group id [{}]@{}".format(group_id, task_id))

        if len(user_guid) > 1:
            raise QueryError("Multiple user guid found for name '{}' and task [{}] ".format(username, task_id))
        return str(user_guid[0][0])
