# -*- coding: utf-8 -*-
import os
import math
import time
import copy
import pickle
import hashlib

from moose.toolbox.image import draw
from moose.models import ModelDownloader
from moose.connection import query, fetch
from moose.utils._os import makedirs, makeparents, npath
from moose.utils.module_loading import import_string
from moose.conf import settings

from .base import IllegalAction, InvalidConfig, SimpleAction

import logging
logger = logging.getLogger(__name__)


class BaseExport(SimpleAction):
    """
    Class to simulate the action of exporting,
    """
    # Object style for a data in records, like 'appname.models.AppnameModel'
    data_model      = ''
    # A class object in 'moose.connection.fetch', inherited `BaseFetcher`
    fetcher_class   = None
    # A class object in 'moose.connection.query', inherited `BaseGuidQuery`,
    # to be passed in `fetcher_class` as the first argument.
    query_class     = None
    # Query context to be passed in `fetcher_class`, find more details in
    # `settings.QUERY_CONTEXT`
    query_context   = {}
    # Exports effective data only?
    effective_only  = True
    # Whether the fetched result to be kept and how long (in hour)
    use_cache       = True
    cache_dirname   = settings.DATACACHE_DIRNAME
    cache_lifetime  = settings.DATACACHE_LIFETIME

    def parse(self, kwargs):
        # Gets config from the kwargs
        config = self.get_config(kwargs)

        # Initialize the fetcher
        if self.fetcher_class:
            self.fetcher = self.fetcher_class(self.query_class, self.query_context)

        # If data_model was defined as a string with dot,
        # for example 'appname.models.AppnameModel'
        if self.data_model:
            self.data_model_cls = import_string(self.data_model)

        # Sets base environment
        environment = {
            'root'   : config.common['root'],
            'relpath': config.common.get('relpath', config.common['root']),
            'task_id': config.upload['task_id'],
            'title'  : config.export['title']
        }

        # Sets custom environment
        self.set_environment(environment, config, kwargs)
        return environment

    def schedule(self, env):
        """
        Generates the context to execute in the following steps.
        """
        task_ids = self.getseq(env['task_id'])
        titles   = self.getseq(env['title'])
        self.assert_equal_size(task_ids, titles)

        # copys the whole environment by default
        for i, (task_id, title) in enumerate(zip(task_ids, titles)):
            context = copy.deepcopy(env)
            context['task_id']  = task_id
            context['title']    = title
            # set custom context if necessary
            self.set_context(context, i)
            yield context


    def get_queryargs(self, context):
        """
        Called by `fetch()` to get arguments for quering database,
        which means, converts `context` to `kwargs`.
        """
        return {
            'project_id': context['task_id'],
            }

    def fetch(self, context):
        """
        Gets queryset with query arguments provided by `get_queryargs()`,
        Dumps the result fetched to a pickle file if `use_cache` was set,
        and loads only if it was not out of the date.
        """
        queryargs = self.get_queryargs(context)
        if self.use_cache:
            # gets the unique identifier by `queryargs`
            cache_id = hashlib.md5(repr(queryargs)).hexdigest()
            cache_pickle = os.path.join(self.app.data_dirname, self.cache_dirname, cache_id)
            if os.path.exists(cache_pickle) and \
                    not self.is_expired(cache_pickle):
                logger.warning("Using cached queryset '%s'." % cache_id)
                with open(cache_pickle) as f:
                    queryset = pickle.load(f)
            else:
                queryset = self.fetcher.fetch(**queryargs)
                makeparents(cache_pickle)
                with open(cache_pickle, 'w') as f:
                    pickle.dump(queryset, f)
        else:
            queryset = self.fetcher.fetch(**queryargs)
        return queryset

    def is_expired(self, filepath):
        """
        Makes sure the file was not created before the warranty period.
        """
        delta = time.time() - os.stat(filepath).st_ctime
        return delta > self.cache_lifetime * 3600


    def execute(self, context):
        """
        Defines how a job was finished in sequence.
        """
        queryset = self.fetch(context)
        self.stats.set_value("query/all", len(queryset))
        for data_model in self.enumerate_model(queryset, context):
            self.handle_model(data_model)
        self.terminate(context)
        return self.get_stats_id(context)

    def enumerate_model(self, queryset, context):
        """
        Generates the model of data to be handled later.
        """
        for item in queryset:
            data_model = self.data_model_cls(item, self.app, self.stats, **context)
            if data_model.is_effective():
                self.stats.inc_value("query/effective")
            else:
                self.stats.inc_value("query/ineffective")
                if self.effective_only:
                    # skips it if export the effective only
                    continue
            yield data_model

    def handle_model(self, data_model):
        """
        Entry point for subclassed actions to handle a data record.
        """
        raise NotImplementedError(\
            'subclasses of BaseExport must provide a handle_model()')

class SimpleExport(BaseExport):
    """
    A simple implementation of the action `export`. Defines the default
    value of query_* properties and performace of handle_model.
    """
    fetcher_class   = fetch.BaseFetcher
    query_class     = query.AllGuidQuery
    query_context   = settings.QUERY_CONTEXT

    download_source = True

    def handle_model_by_callback(self, queryset, callback, context):
        downloader = ModelDownloader(callback, self.stats)
        downloader.start()

        for data_model in self.enumerate_model(queryset, context):
            data_model.set_up()
            downloader.add_task(data_model)

        downloader.join()

    def execute(self, context):
        """
        Defines how a job was finished in sequence.
        """
        queryset = self.fetch(context)
        if self.download_source:
            self.handle_model_by_callback(queryset, self.handle_model, context)
        else:
            for data_model in self.enumerate_model(queryset, context):
                self.handle_model(data_model)
        self.terminate(context)
        return self.get_stats_id(context)

    def handle_model(self, data_model):
        self.dump(data_model)

    def dump(self, data_model):
        # creates the upper directory to save json files
        makeparents(data_model.dest_filepath)
        filename, _ = os.path.splitext(data_model.dest_filepath)
        with open(filename+data_model.output_suffix, 'w') as f:
            f.write(data_model.to_string())

class TaskExport(SimpleExport):
    """
    Only `task id` is required, field `title` and `batch` were to be queried
    automatically.
    """

    task_query_class = query.ProjectInfoQuery


    def parse(self, kwargs):
        # Gets config from the kwargs
        config = self.get_config(kwargs)

        # Initialize the fetcher
        if self.fetcher_class:
            self.fetcher = self.fetcher_class(self.query_class, self.query_context)

        # If data_model was defined as a string with dot,
        # for example 'appname.models.AppnameModel'
        if self.data_model:
            self.data_model_cls = import_string(self.data_model)

        # Sets base environment
        environment = {
            'root'   : config.common['root'],
            'relpath': config.common.get('relpath', config.common['root']),
            'task_id': config.upload['task_id'],
        }

        # Sets custom environment
        self.set_environment(environment, config, kwargs)
        return environment


    def schedule(self, env):
        """
        Except for passing field from `env` to `context`, but also get `title`
        and `batch` from the database.
        """
        task_ids = self.getseq(env['task_id'])
        self.task_querier = self.task_query_class.create_from_context(self.query_context)

        # copys the whole environment by default
        for i, task_id in enumerate(task_ids):
            task_info = self.task_querier.query(project_id=task_id)[0]
            context = copy.deepcopy(env)
            context.update({
                'task_id': task_id,
                'title': task_info[2],
                'batch': task_info[4],
            })
            # set custom context if necessary
            self.set_context(context, i)
            yield context


class ImagesExport(TaskExport):
    """
    Downloads source files meanwhile draws mask and blended pictures
    """
    # A table of labels mapping to colors
    pallet       = None
    mask_label  = '_mask'
    blend_label = '_blend'
    image_suffix  = '.png'

    def handle_model(self, data_model):
        self.dump(data_model)
        self.draw(data_model)

    def draw(self, data_model):
        image_path = data_model.dest_filepath
        image_prefix, _ = os.path.splitext(image_path)
        try:
            # no mask or blend images if setting labels None
            if self.mask_label:
                mask_path = image_prefix + self.mask_label + self.image_suffix
                draw.draw_polygons(image_path, mask_path, data_model.datalist, self.pallet)
            if self.blend_label:
                blend_path = image_prefix + self.blend_label + self.image_suffix
                draw.blend(image_path, blend_path, data_model.datalist, self.pallet)
        except AttributeError as e:
            logger.error("Unable to read {}.".format(npath(image_path)))
