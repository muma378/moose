# -*- coding: utf-8 -*-
import os
import math
import time
import pickle
import hashlib
import logging

from moose.utils._os import makedirs, makeparents
from moose.connection import query, database, fetch
from moose.utils.module_loading import import_string
from moose.conf import settings
from moose.utils.serialize import dump_xlsx
from .base import IllegalAction, InvalidConfig, SimpleAction
from .download import download, DownloadStat, DataModelDownloader
from .exports import BaseExport

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

    person_query_class = query.UsersInProjectQuery
    name_suffix = '_info'

    def query_person_info(self, context):
        querier = self.person_query_class.create_from_context(self.query_context)
        person_info = querier.query(project_id=context['task_id'])
        return person_info

    def get_info_table(self, person_info):
        return {x[0]: x[1:] for x in person_info}

    def handle_model(self, data_model, workbook):
        workbook.append(data_model.to_row())
        return ''

    def execute(self, context):
        """

        """
        queryset = self.fetch(context)
        person_info = self.query_person_info(context)
        context['users_table'] = self.get_info_table(person_info)
        output = []
        workbook = []
        print(person_info)
        for data_model in self.enumerate_model(queryset, context):
            output.append(self.handle_model(data_model, workbook))
        dest_info_file = os.path.join(self.app.data_dirname, context['title']+self.name_suffix+'.xlsx')
        dump_xlsx(workbook, dest_info_file)
        return '\n'.join(output)
