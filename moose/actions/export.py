# -*- coding: utf-8 -*-
import os
import math
import time
import pickle
import logging

from moose.connection import query
from moose.connection import database
from moose.connection import fetch
from moose.connection.cloud import azure
from moose.utils._os import makedirs, makeparents
from moose.utils.module_loading import import_string
from moose.conf import settings

from .base import AbstractAction, IllegalAction
from .download import download, DownloadStat

print(
    "Package 'moose.actions.export' is deprecative, please consider "
    "using 'moose.actions.exports'.")

logger = logging.getLogger(__name__)

class BaseExport(AbstractAction):
    """
    Class to simulate the action of exporting, 5 procedures are accomplished
    in sequence:

    `get_context`
        Converts config object to a dict of context.

    `parse`
        Entry for subclass to get the user-defined data.

    `fetch`
        Query and fetch annotation data from the database.

    `handle`
        Entry for subclass to
    """
    # model to represent a data record
    data_model = ''
    query_class = None
    fetcher_class = None
    query_context = {}
    # exports effective data only
    effective_only = True

    def get_context(self, kwargs):
        if kwargs.get('config'):
            config = kwargs.get('config')
        else:
            logger.error("Missing argument: 'config'.")
            raise IllegalAction(
                "Missing argument: 'config'. This error is not supposed to happen, "
                "if the action class was called not in command-line, please provide "
                "the argument `config = config_loader._parse()`.")

        if self.fetcher_class:
            self.fetcher = self.fetcher_class(self.query_class, self.query_context)

        context = {
            'root': config.common['root'],
            'relpath': config.common['relpath'],
            'task_id': config.upload['task_id'],
            'title': config.export['title']
        }

        context.update(self.parse(config, kwargs))
        return context

    def parse(self, config, kwargs):
        return {}

    def fetch(self, task_id, context):
        raise NotImplementedError

    def handle(self, model, context):
        pass

    def run(self, **kwargs):
        environment = self.get_context(kwargs)
        output = []
        for context in self.schedule(environment):
            self.handle(context)


    def run(self, **kwargs):
        context = self.get_context(kwargs)
        queryset = self.fetch(context['task_id'], context)
        output = []
        neffective = 0
        data_model_cls = import_string(self.data_model)
        for item in queryset:
            dm = data_model_cls(item, **context)
            if dm.is_effective():
                neffective += 1
                self.handle(dm, context)

        output.append("%d results processed." % neffective)
        return '\n'.join(output)

class SimpleExport(BaseExport):
    query_class = query.AllGuidQuery
    fetcher_class = fetch.BaseFetcher
    query_context = settings.QUERY_CONTEXT
    use_cache = True
    warranty_period = 1     # hour

    def handle(self, model, context):
        title = context['title']
        dst = os.path.join(self.app.data_dirname, title)
        self.dump(model, dst)

    def dump(self, model, dst):
        filepath = os.path.join(dst, model.normpath)
        makeparents(filepath)
        filename, _ = os.path.splitext(filepath)
        with open(filename+model.output_suffix, 'w') as f:
            f.write(model.to_string())

    def is_expired(self, filepath):
        delta = time.time() - os.stat(filepath).st_ctime
        return delta > self.warranty_period * 3600

    def fetch(self, task_id, context):
        if self.use_cache:
            cache_pickle = os.path.join(self.app.data_dirname, str(task_id)+'.pickle')
            if os.path.exists(cache_pickle) and not self.is_expired(cache_pickle):
                logger.warning("Using cached queyrset of task '%s'." % task_id)
                with open(cache_pickle) as f:
                    queryset = pickle.load(f)
            else:
                queryset = self.fetcher.fetch(project_id=task_id)
                with open(cache_pickle, 'w') as f:
                    pickle.dump(queryset, f)
        else:
            queryset = self.fetcher.fetch(project_id=task_id)
        return queryset


class DownloadAndExport(SimpleExport):
    """
    Downloads raw files meanwhile exporting the result.
    """
    overwrite_conflict = False

    def run(self, **kwargs):
        context = self.get_context(kwargs)
        task_id = context['task_id']
        queryset = self.fetch(task_id, context)
        output = []
        urls = []
        neffective = 0

        data_model_cls = import_string(self.data_model)
        models = []
        for item in queryset:
            dm = data_model_cls(item, **context)
            if dm.is_effective():
                neffective += 1
                models.append(dm)
                urls.append((dm.filelink(context['task_id']), dm.filepath))

        dst = os.path.join(self.app.data_dirname, context['title'])
        stat = download(urls, dst, overwrite=self.overwrite_conflict)
        output.append(str(stat))

        for dm in models:
            self.handle(dm, context)
        output.append("%d results processed." % neffective)

        return '\n'.join(output)
