# -*- coding: utf-8 -*-
import os
import math
import json
from collections import defaultdict

from moose.connection.cloud import AzureBlobService
from moose.shortcuts import ivisit
from moose.conf import settings
from moose.utils.encoding import smart_text
from moose.utils.datautils import islicel

from .base import AbstractAction, IllegalAction

import logging
logger = logging.getLogger(__name__)


class BaseUpload(AbstractAction):
    """
    Class to simulate the action of uploading, 5 procedures are accomplished
    in sequence:
    `
    Get-Context -> Enumerate-Files -> Upload -> Write-Index
    `
    while the following steps are implemented by subclasses.

    `parse`
        Get extra info to update context.

    `partition`
        Valid files are distinguished from the invalid.

    `split`
        Controls how data were distributed into groups.

    `index`
        Returns a catalog list uoloaded files.

    `to_string`
        Convert the list of index to string(json).

    """
    use_azure = True
    gen_index = True
    default_pattern = None

    def get_context(self, kwargs):
        if self.use_azure:
            azure_setting = kwargs.get('azure', settings.AZURE)

            if azure_setting:
                self.azure = AzureBlobService(azure_setting)
            else:
                logger.error("Missing argument: 'azure'")
                raise IllegalAction(
                    "Missing argument: 'azure'. If you were not going to "
                    "use 'azure' in the action, please set class varaible "
                    "'use_azure' to False.")

        if kwargs.get('config'):
            config = kwargs.get('config')
        else:
            logger.error("Missing argument: 'config'.")
            raise IllegalAction(
                "Missing argument: 'config'. This error is not supposed to happen, "
                "if the action class was called not in command-line, please provide "
                "the argument `config = config_loader._parse()`.")

        context = {
            'root': config.common['root'],
            'relpath': config.common['relpath'] if config.common['relpath'] else config.common['root'],
            'task_id': config.upload['task_id'],
        }

        context.update(self.parse(config, kwargs))
        return context

    def parse(self, config, kwargs):
        """
        Entry point for subclassed upload actions to update context.
        """
        return {}

    def lookup_files(self, root, context):
        """
        Finds all files located in root which matches the given pattern.
        """
        pattern     = context.get('pattern', self.default_pattern)
        ignorecase  = context.get('ignorecase', True)
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

    def check_file(self, filepath):
        """
        Entry point for subclassed upload actions to remove unwanted files.
        """
        return True

    def enumerate(self, context):
        """
        List files to upload and belonged container.
        """
        files = self.lookup_files(context['root'], context)
        passed, removed = self.partition(files, context)

        blob_pairs = []
        relpath = context['relpath']
        for filepath in passed:
            blobname = os.path.relpath(filepath, relpath)
            if not self.check_file(filepath):
                continue
            blob_pairs.append((blobname, filepath))
        logger.debug("%d files are effective finally." % len(blob_pairs))

        for task_id, blob_pairs in self.split(blob_pairs, context):
            yield task_id, blob_pairs

    def split(self, blob_pairs, context):
        """
        Files are splited into different groups and returns in order.
        """
        task_id = context['task_id']
        yield task_id, blob_pairs

    def index(self, blob_pairs, context):
        """
        Entry point for subclassed to generate a catalog.
        """
        raise NotImplementedError

    def to_sting(self, catalog):
        raise NotImplementedError

    def run(self, **kwargs):
        context = self.get_context(kwargs)
        enumerater = self.enumerate(context)

        output = []
        for container_name, blob_pairs in enumerater:
            if self.use_azure:
                blobs = self.azure.upload(container_name, blob_pairs)
                output.append("%s files were uploaded to [%s]." % (len(blobs), container_name))

            if self.gen_index:
                index_file = os.path.join(self.app.data_dirname, container_name+'.json')
                catalog = self.index(blob_pairs, context)
                with open(index_file, 'w') as f:
                    f.write(self.to_string(catalog))
                output.append("Index was written to '%s'." % index_file)

        return '\n'.join(output)


class SimpleUpload(BaseUpload):
    """
    The common way to upload files and generate a catalog.
    """
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
    """
    use_azure = False

    def lookup_files(self, context):
        refered_task = context['refered_task']
        blob_names = self.azure.list_blobs(refered_task)
        return blob_names

    def enumerate(self, context):
        """
        List files to upload and belonged container.
        """
        files = self.lookup_files(context)
        passed, removed = self.partition(files, context)

        relpath = context['relpath']
        refered_task = context['refered_task']
        for blobname in passed:
            filepath = os.path.join(relpath, blobname)
            if not self.check_file(filepath):
                continue

            url = settings.AZURE_FILELINK.format(task_id=refered_task, file_path=blobname)
            blob_pairs.append((url, blobname))
        logger.debug("%d files are effective finally." % len(blob_pairs))

        for task_id, blob_pairs in self.split(blob_pairs, context):
            yield task_id, blob_pairs

    def index(self, blob_pairs, context):
        catalog = []
        for url, blobname in blob_pairs:
            catalog.append({
                'url': url ,
                'dataTitle': blobname,
            })
        return catalog


class MultipleUpload(SimpleUpload):
    """
    Upload multiple tasks in an action.
    """
    def parse(self, config, kwargs):
        return {
            # optional fields
            'nshare' : config.upload.get('nshare', 1),
            'pattern': config.upload.get('pattern', None),
        }

    def split(self, blob_pairs, context):
        nshare = int(context['nshare'])
        num_per_share = int(math.ceil(len(blob_pairs)*1.0/nshare))
        if nshare != 1:
            logger.debug("%d files are to upload on average for each time." % num_per_share)

        task_id = context['task_id']
        container_names = task_id if isinstance(task_id, list) else [task_id, ]

        if len(container_names) != nshare:
            logger.error("Number of containers is not equal to nshare.")
            raise IllegalAction("Number of containers is not equal to nshare.")

        for i, container_name in enumerate(container_names):
            start = i * num_per_share
            end = min(start+num_per_share, len(blob_pairs))
            yield container_name, blob_pairs[start:end]


class DirsUpload(SimpleUpload):
    remove_dirname = True

    def parse(self, config, kwargs):
        return {
            'dirnames': [ smart_text(x) for x in config.upload.get('dirnames', [''])]
        }

    def split(self, all_blob_pairs, context):
        task_ids = context['task_id']
        dirnames = context['dirnames']
        for dirname, task_id in zip(dirnames, task_ids):
            sub_blob_pairs = filter(lambda x: dirname in x[1], all_blob_pairs)
            if self.remove_dirname:
                sub_blob_pairs = [ (os.path.relpath(x[0], dirname), x[1]) for x in sub_blob_pairs]
            yield str(task_id), sub_blob_pairs

class VideosUpload(SimpleUpload):
    nframes_per_item = 300
    use_short_name = True
    hostname = 'http://crowdfile.blob.core.chinacloudapi.cn/'
    image_suffix = 'jpg'

    def index(self, blob_pairs, context):
        catalog = []
        groups = self.group(blob_pairs)
        for dirname, filenames in groups.items():
            title = os.path.basename(dirname)
            for i, names in islicel(filenames, self.nframes_per_item):
                catalog.append({
                    'title': title+'-'+str(i+1),
                    'itype': self.image_suffix,
                    'puri': self.hostname,
                    'images': [{'src': os.path.splitext(x)[0]} for x in names]
                })
        return catalog

    def group(self, blob_pairs):
        """
        Groups files by dirnames.
        """
        groups = defaultdict(list)
        for blobname, filename in blob_pairs:
            dirname = os.path.dirname(filename)
            groups[dirname].append(blobname)
        return groups

    def enumerate(self, context):
        """
        List files to upload and belonged container.
        """
        files = self.lookup_files(context['root'], context)
        passed, removed = self.partition(files, context)

        blob_pairs = []
        relpath = context['relpath']
        for filepath in passed:
            blobname = os.path.relpath(filepath, relpath)
            if not self.check_file(filepath):
                continue
            blob_pairs.append((blobname, filepath))
        logger.debug("%d files are effective finally." % len(blob_pairs))

        from moose.utils.shortname import build_trie
        if self.use_short_name:
            self.name_mapper = {}
            tree = build_trie([x[0] for x in blob_pairs])
            import pdb; pdb.set_trace()

        for task_id, blob_pairs in self.split(blob_pairs, context):
            yield task_id, blob_pairs

    def run(self, **kwargs):
        context = self.get_context(kwargs)
        enumerater = self.enumerate(context)

        output = []
        for container_name, blob_pairs in enumerater:
            if self.use_azure:
                blobs = self.azure.upload(container_name, blob_pairs)
                output.append("%s files were uploaded to [%s]." % (len(blobs), container_name))

            if self.gen_index:
                index_file = os.path.join(self.app.data_dirname, container_name+'.json')
                catalog = self.index(blob_pairs, context)
                with open(index_file, 'w') as f:
                    f.write(self.to_string(catalog))
                output.append("Index was written to '%s'." % index_file)

        return '\n'.join(output)
