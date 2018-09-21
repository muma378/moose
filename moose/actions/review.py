# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import math
import time
import pickle
import hashlib

from moose.utils._os import makedirs, makeparents
from moose.connection import database, query, fetch
from moose.utils.module_loading import import_string
from moose.conf import settings
from moose.utils.serialize import dump_xlsx

from .export import BaseExport

import logging
logger = logging.getLogger(__name__)

def getseq(list_or_ele):
    return list_or_ele if isinstance(list_or_ele, list) else [list_or_ele, ]


class BaseReview(BaseExport):
    """
    Class to simulate the action of reviewing all records
    """
    fetcher_class   = fetch.BaseFetcher
    query_class     = query.AllGuidQuery
    query_context   = settings.QUERY_CONTEXT

    def handle_model(self, data_model):
        pass

class SimpleReview(BaseReview):

    person_query_class = query.TeamUsersInProjectQuery
    name_suffix = '_info'

    # Sets custom environment
    def set_environment(self, env, config, kwargs):
        self.workbook = []
        self.dest_filepath = os.path.join(self.app.data_dirname, env['name']+'.xlsx')


    def query_person_info(self, context):
        querier = self.person_query_class.create_from_context(self.query_context)
        person_info = querier.query(project_id=context['task_id'])
        return person_info

    def get_info_table(self, person_info):
        return {x[0]: x[1:] for x in person_info}

    def handle_model(self, data_model):
        self.workbook.append(data_model.overview())
        return ''

    def execute(self, context):
        queryset = self.fetch(context)
        person_info = self.query_person_info(context)
        context['users_table'] = self.get_info_table(person_info)
        output = []
        # print(person_info)
        for data_model in self.enumerate_model(queryset, context):
            output.append(self.handle_model(data_model))
        self.terminate(context)
        return '\n'.join(output)

    def teardown(self, env):
        dump_xlsx(self.workbook, self.dest_filepath)
