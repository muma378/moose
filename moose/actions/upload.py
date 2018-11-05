# -*- coding: utf-8 -*-
import os
import math
import json
import copy
from collections import defaultdict

from moose.conf import settings
from moose.shortcuts import ivisit
from moose.utils._os import safe_join
from moose.utils.encoding import smart_text
from moose.utils.datautils import islicel
from moose.connection.cloud import AzureBlobService

from .base import IllegalAction, InvalidConfig, SimpleAction

import logging
logger = logging.getLogger(__name__)


class BaseUpload(SimpleAction):
    """

    """
    upload_files    = True
    overwrite       = False
    # default to settings.AZURE
    azure_setting   = settings.AZURE
    generate_index  = True
    default_pattern = None
    ignorecase      = True

    def parse(self, kwargs):
        # Gets config from the kwargs
        config = self.get_config(kwargs)

        # uses the custom settings if defined
        if self.azure_setting:
            self.azure = AzureBlobService(self.azure_setting)

        environment = {
            # base dirname for files to upload
            'root'   : config.common['root'],
            # part to remove for blob name, use root by default
            'relpath': config.common.get('relpath', config.common['root']),
            'task_id': config.upload['task_id'],
            # provided if multiple dirnames for multiple tasks
            'dirs'   : config.upload.get('dirs'),
        }

        self.set_environment(environment, config, kwargs)
        return environment

    def lookup_files(self, root, context):
        """
        Finds all files located in root which matches the given pattern.
        """
        pattern     = context.get('pattern', self.default_pattern)
        ignorecase  = context.get('ignorecase', self.ignorecase)
        logger.debug("Visit '%s' with pattern: %s..." % (root, pattern))

        files   = []
        for filepath in ivisit(root, pattern=pattern, ignorecase=ignorecase):
            files.append(filepath)
        logger.debug("%d files found." % len(files))
        return files

    def partition(self, files, context):
        """
        Entry point for subclassed upload actions to remove unwanted files.
        """
        return files, []

    def get_blob_pairs(self, files, relpath):
        """
        Converts filepath to (blobname, filepath) while blobname is the
        relative path to `relpath`.
        """
        blob_pairs = []
        for filepath in files:
            blobname = os.path.relpath(filepath, relpath)
            if not self.check_file(filepath):
                continue
            blob_pairs.append((blobname, filepath))
        return blob_pairs

    def check_file(self, filepath):
        """
        Entry point for subclassed upload actions to remove unwanted files.
        """
        return True

    def index(self, blob_pairs, context):
        """
        Entry point for subclassed to generate a catalog.
        """
        raise NotImplementedError

    def to_string(self, catalog):
        raise NotImplementedError

    def get_all_files(self, context):
        return self.lookup_files(context['root'], context)

    def execute(self, context):
        files = self.get_all_files(context)
        self.stats.set_value("files/all", len(files))

        passed, removed = self.partition(files, context)
        self.stats.set_value("files/passed", len(passed))
        self.stats.set_value("files/removed", len(removed))
        blob_pairs = self.get_blob_pairs(passed, context['relpath'])

        container_name = context['task_id']
        if self.upload_files:
            self.stats.set_value("upload/total", len(blob_pairs))
            blobs = self.azure.upload(container_name, blob_pairs, overwrite=self.overwrite)
            self.stats.set_value("upload/upload", len(blobs))
            self.output.append("%s files were uploaded to [%s]." % (len(blobs), container_name))

        if self.generate_index:
            index_file = safe_join(self.app.data_dirname, container_name+'.json')
            catalog = self.index(blob_pairs, context)
            with open(index_file, 'w') as f:
                f.write(self.to_string(catalog))
            self.output.append("Index was written to '%s'." % index_file)

        self.terminate(context)
        return self.get_stats_id(context)


class SimpleUpload(BaseUpload):
    """
    The common way to upload files and generate a catalog.
    """
    def schedule(self, env):
        task_ids = self.getseq(env['task_id'])
        if env.get('dirs'):
            dirs = self.getseq(env['dirs'])
        else:
            dirs = ['', ]
        self.assert_equal_size(task_ids, dirs)
        root = env['root']

        for i, (task_id, dirname) in enumerate(zip(task_ids, dirs)):
            context = copy.deepcopy(env)
            context['root']     = os.path.join(root, dirname)
            context['task_id']  = str(task_id)
            self.set_context(context, i)
            yield context

    def index(self, blob_pairs, context):
        catalog = []
        for blobname, filename in blob_pairs:
            catalog.append({
                'url': blobname,
                'dataTitle': blobname,
            })
        return catalog

    def to_string(self, catalog):
        items = []
        for item in catalog:
            items.append(
                json.dumps(item, ensure_ascii=False).encode(settings.FILE_CHARSET)
                )
        return '\n'.join(items)


class ReferredUpload(SimpleUpload):
    """
    Do not do actual upload, but refers the old filelinks.
    Pass `refer` as an option in environment
    """
    upload_files = False

    def get_all_files(self, context):
        referred_task = context['refer']
        blob_names = self.azure.list_blobs(referred_task)
        return blob_names

    def get_blob_url(self, task_id, blobname):
        return settings.AZURE_FILELINK.format(task_id=task_id, file_path=blobname)

    def get_blob_pairs(self, files, relpath):
        """
        Converts filepath to (blobname, blob_url)
        """
        refer      = context['refer']
        blob_pairs = [(f, self.get_blob_url(refer, f)) for f in files]
        return blob_pairs

    def index(self, blob_pairs, context):
        catalog = []
        for blobname, blob_url in blob_pairs:
            catalog.append({
                'url': blob_url,
                'dataTitle': blobname,
            })
        return catalog


class VideosUpload(SimpleUpload):
    image_suffix = 'jpg'
    use_short_name = False
    nframes_per_item = 300
    hostname = 'http://crowdfile.blob.core.chinacloudapi.cn/'

    def index(self, blob_pairs, context):
        catalog = []
        groups = self.group(blob_pairs)
        for dirname, blobnames in groups.items():
            title = os.path.basename(dirname)
            for i, names in islicel(blobnames, self.nframes_per_item):
                catalog.append({
                    'title': title+'-'+str(i+1),
                    'itype': self.image_suffix,
                    'puri': self.hostname,
                    'images': [{'src': os.path.splitext(x)[0]} for x in names]
                })
        return catalog

    def group(self, blob_pairs, key=None):
        """
        Groups files by dirnames.
        """
        if not key:
            # groups by dirname by default
            key = lambda x: os.path.dirname(x)

        # clustering groups by keys
        groups = defaultdict(list)
        for blobname, filename in blob_pairs:
            groups[key(filename)].append(blobname)

        # then sorts each groups
        for k in groups.keys():
            groups[k].sort()
        return groups


class AverageUpload(SimpleUpload):
    """
    Upload multiple tasks in an action.
    """
    def set_environment(self, env, config, kwargs):
        # optional fields
        env['nshare'] = config.upload.get('nshare', 1)

    def get_roots(self, env):
        """
        Defines which root to use to look up files.
        """
        return self.getseq(env['root'])

    def schedule(self, env):
        """
        List files to upload and belonged container.
        """
        task_ids = self.getseq(env['task_id'])
        nshare = int(env['nshare'])
        self.assert_equal_size(task_ids, range(nshare))

        files = []
        for root in self.get_roots(env):
            files.extend(self.lookup_files(root, env))
        logger.debug("%d files are effective finally." % len(files))

        num_per_share = int(math.ceil(len(files)*1.0/nshare))

        for i, task_id in enumerate(task_ids):
            context = copy.deepcopy(env)
            context['task_id']  = task_id
            # get a slice of files for one time
            start = i * num_per_share
            end   = min(start+num_per_share, len(files))
            context['files'] = files[start:end]
            self.set_context(context, i)
            yield context

    def get_all_files(self, context):
        return context['files']
