# -*- coding: utf-8 -*-
import os
import math
import time
import copy
import pickle
import hashlib
import logging

from moose.process.image import draw
from moose.utils._os import makedirs, makeparents, npath
from moose.connection import query, database, fetch
from moose.utils.module_loading import import_string
from moose.conf import settings

from .base import IllegalAction, InvalidConfig, SimpleAction
from .download import download, DownloadStat, DataModelDownloader

logger = logging.getLogger(__name__)

def getseq(list_or_ele):
    return list_or_ele if isinstance(list_or_ele, list) else [list_or_ele, ]


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
    warranty_period = 1

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
            'relpath': config.common['relpath'],
            'task_id': config.upload['task_id'],
            'title'  : config.export['title']
        }

        # Sets custom environment
        self.set_environment(environment, config, kwargs)
        return environment

    def set_environment(self, env, config, kwargs):
        """
        Entry point for subclassed actions to add custom environment.
        """
        pass

    def schedule(self, env):
        """
        Generates the context to execute in the following steps.
        """
        task_ids = getseq(env['task_id'])
        titles = getseq(env['title'])
        if len(task_ids) != len(titles):
            raise InvalidConfig(
                "The number of values in options `task_id` and `title` is not equal.")

        # copys the whole environment by default
        for i, (task_id, title) in enumerate(zip(task_ids, titles)):
            context = copy.deepcopy(env)
            context['task_id']  = task_id
            context['title']    = title
            # set custom context if necessary
            self.set_context(context, i)
            yield context

    def set_context(self, context, i):
        """
        Entry point for subclassed actions to add custom context.
        """
        pass

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
            cache_pickle = os.path.join(self.app.data_dirname, cache_id)
            if os.path.exists(cache_pickle) and \
                    not self.is_expired(cache_pickle):
                logger.warning("Using cached queryset '%s'." % cache_id)
                with open(cache_pickle) as f:
                    queryset = pickle.load(f)
            else:
                queryset = self.fetcher.fetch(**queryargs)
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
        return delta > self.warranty_period * 3600

    def execute(self, context):
        """
        Defines how a job was finished in sequence.
        """
        queryset = self.fetch(context)
        self.stats.set_value("query/all", len(queryset))
        for data_model in self.enumerate_model(queryset, context):
            self.handle_model(data_model)

    def enumerate_model(self, queryset, context):
        """
        Generates the model of data to be handled later,

        """
        for item in queryset:
            data_model = self.data_model_cls(item, app=self.app, **context)
            if self.effective_only and not data_model.is_effective():
                self.stats.inc_value("query/ineffective")
                continue
            self.stats.inc_value("query/effective")
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

    def execute(self, context):
        """
        Defines how a job was finished in sequence.

        """
        queryset = self.fetch(context)
        output = []
        if self.download_source:
            self.downloader = DataModelDownloader(self.handle_model, self.stats)
            self.downloader.start()

            for data_model in self.enumerate_model(queryset, context):
                self.downloader.add_task(data_model)

            self.downloader.join()
        else:
            for data_model in self.enumerate_model(queryset, context):
                self.handle_model(data_model)
        return '\n'.join(output)

    def handle_model(self, data_model):
        self.dump(data_model)
        data_model.stats(self.stats)

    def dump(self, data_model):
        # creates the upper directory to save json files
        makeparents(data_model.dest_filepath)
        filename, _ = os.path.splitext(data_model.dest_filepath)
        with open(filename+data_model.output_suffix, 'w') as f:
            f.write(data_model.to_string())

class ImagesExport(SimpleExport):
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
            mask_path = image_prefix + self.mask_label + self.image_suffix
            draw.draw_polygons(image_path, mask_path, data_model.datalist, self.pallet)
            blend_path = image_prefix + self.blend_label + self.image_suffix
            draw.blend(image_path, blend_path, data_model.datalist, self.pallet)
        except AttributeError as e:
            logger.error("Unable to read {}.".format(npath(image_path)))
