# -*- coding: utf-8 -*-
import os
import math
import logging

from moose.connection.cloud import AzureBlobService
from moose.shortcuts import ivisit
from moose.conf import settings

from .base import AbstractAction, IllegalAction

logger = logging.getLogger(__name__)

class BaseUpload(AbstractAction):
    """
    Class to simulate the action of uploading, 5 procedures are accomplished
    in sequence:

    `parse`
        Converts config object to a dict of context.

    `explore`
        Enumerates files according to arguments 'root', 'suffix', etc.

    `schedule`
        Controls how data were distributed into groups.

    `upload`
        Uploading.

    `index`
        Generates an index file.

    """
    def parse(self, kwargs):
        if kwargs.get('app'):
            self.app = kwargs['app']
        else:
            raise IllegalAction("Missing argument: 'app_config'.")

        config = kwargs.get('config')
        azure_setting = kwargs.get('azure', settings.AZURE)

        if kwargs.get('config'):
            config = kwargs.get('config')
        else:
            logger.error("Missing argument: 'config'.")
            raise IllegalAction("Missing argument: 'config'.")

        context = {
            'root': config.common['root'],
            'relpath': config.common['relpath'],
            'task_id': config.upload['task_id'],

            # optional fields
            'nshare' : config.upload.get('nshare', 1),
            'pattern': config.upload.get('pattern', None),
            'maximum': config.upload.get('maximum', None),
            'exclude': config.upload.get('exclude', []),
        }

        if isinstance(context['exclude'], str) or isinstance(context['exclude'], int):
            context['exclude'] = [context['exclude'], ]


        if azure_setting:
            self.azure = AzureBlobService(azure_setting)
        else:
            logger.error("Missing argument: 'azure'")
            raise IllegalAction("Missing argument: 'azure'")

        if isinstance(context['task_id'], list) and len(context['task_id']) != (context['nshare']):
            raise IllegalAction('The number of tasks and shares are not equal.')

        return context

    def explore(self, context):
        files = []
        root = context['root']
        pattern = context['pattern']
        logger.debug("Visit '%s' with pattern: %s..." % (root, pattern))
        for filepath in ivisit(root, pattern=pattern, ignorecase=True):
            files.append(filepath)
        logger.debug("%d files found." % len(files))
        return files

    def check_file(self, filepath):
        return True

    def schedule(self, files, context):
        excluded_blobs = []
        exclude = context.get('exclude')
        if exclude:
            for excluded_container in exclude:
                excluded_blobs.extend(self.azure.list_blobs(excluded_container))
            logger.debug("%d files found in bypast [%s]." % \
                (len(excluded_blobs), ','.join(exclude)))

        blob_pairs = []
        relpath = context.get('relpath')
        for filepath in files:
            blob_name = os.path.relpath(filepath, relpath)
            if blob_name in excluded_blobs:
                continue
            if not self.check_file(filepath):
                continue
            blob_pairs.append((blob_name, filepath))
        logger.debug("%d files are effective finally." % len(blob_pairs))

        nshare = int(context['nshare'])
        num_per_share = int(math.ceil(len(blob_pairs)*1.0/nshare))
        if nshare != 1:
            logger.debug("%d files are to upload on average for each time." % num_per_share)

        task_id = context['task_id']
        container_names = task_id if isinstance(task_id, list) else [task_id, ]
        for i, container_name in enumerate(container_names):
            start = i * num_per_share
            end = min(start+num_per_share, len(blob_pairs))
            yield container_name, blob_pairs[start:end]

    def index(self, blob_pairs, context):
        return '\n'.join([pairs[0] for pairs in blob_pairs])

    def run(self, **kwargs):
        context = self.parse(kwargs)
        files = self.explore(context)
        output = []
        for container_name, blob_pairs in self.schedule(files, context):
            blobs = self.azure.upload(container_name, blob_pairs)
            index_file = os.path.join(self.app.data_dirname, container_name+'.json')
            with open(index_file, 'w') as f:
                f.write(self.index(blob_pairs, context))
                logger.info("Index content are written to: %s" % index_file)
            output.append("%s files were uploaded to [%s]." % (len(blobs), container_name))
        return '\n'.join(output)
