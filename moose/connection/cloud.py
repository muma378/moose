# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import urllib
from azure.storage.blob import BlockBlobService, PublicAccess
from azure.common import AzureConflictHttpError, AzureMissingResourceHttpError

from moose.core.exceptions import ImproperlyConfigured
from moose.utils import progressbar
from moose.utils.encoding import escape_uri_path
from moose.utils._os import npath, ppath, safe_join, normpath
from moose.conf import settings
from moose.shortcuts import get_matchfn
import re
import logging
logger = logging.getLogger(__name__)

class AzureBlobService(object):
    """
    Application interface to access <Azure Blob Storage Service>. A wrapper of
    the module 'BlockBlobService' from azure SDK for python.
    """

    blob_pattern = 'http://([\w\.]+)/(\w+)/(.*)'


    def __init__(self, settings_dict):
        # Set settings for azure connections
        self.settings_dict = settings_dict
        self.widgets = [ progressbar.Percentage(), ' ', progressbar.Bar(),
            ' ', progressbar.ETA()]

        self.account = settings_dict['ACCOUNT']
        self.host = settings_dict['ACCOUNT']+'.blob.'+settings_dict['ENDPOINT']
        logger.debug("Connectings to '%s'..." % self.host)
        self.block_blob_service = BlockBlobService(
            account_name=settings_dict['ACCOUNT'],
            account_key=settings_dict['KEY'],
            endpoint_suffix=settings_dict['ENDPOINT'])
        logger.debug("Connection established.")

    def create_container(self, container_name, set_public=False):
        """
        Create a azure blob container.
        """
        logger.debug("Creating container [%s] on '%s'." % (container_name, self.host))

        if set_public:
            public_access = PublicAccess.Container
            logger.debug("Set container [%s] access to public." % container_name)
        else:
            public_access = None

        try:
            result = self.block_blob_service.create_container(
                container_name, fail_on_exist=True,
                timeout=self.settings_dict['TIMEOUT'],
                public_access=public_access)
        except AzureConflictHttpError as e:
            logger.error("The specified container [%s] already exists." % container_name)
            result = False

        logger.info("Container created: %s." % container_name)
        return result

    def list_containers(self, prefix=None):
        logger.debug("Request sent to list all containers on '%s'." % self.host)
        # An iterator to list all containers on blob
        icontainers = self.block_blob_service.list_containers(
            prefix=prefix, timeout=self.settings_dict['TIMEOUT'])

        # Converts an iterator to list
        container_names = [container for container in icontainers]

        logger.info(
            "%d containers found on '%s'." % (len(container_names), self.host)
            )
        return container_names


    def list_blobs(self, container_name, prefix=None, suffix=None):
        """
        Lists all blobs on the container, note that the blob_names returned
        are posix-style path, no matter what names were when create.
        """
        blob_names = []
        logger.debug("Request to list blobs in container [%s]." % container_name)

        try:
            # An iterator to
            iblobs = self.block_blob_service.list_blobs(
                container_name, prefix=prefix, timeout=self.settings_dict['TIMEOUT'])

            if suffix:
                blob_names = [blob.name for blob in iblobs if blob.name.endswith(suffix)]
            else:
                blob_names = [blob.name for blob in iblobs]

        except AzureMissingResourceHttpError as e:
            logger.error(
                "The specified container [%s] does not exist." % container_name
                )

        logger.info(
            "%d blobs found on [%s]." % (len(blob_names), container_name)
            )
        return blob_names


    def create_blob_from_path(self, container_name, blob_name, filepath):
        """
        Uploads a file to the container.

        Returns an instance of `Blob` with properties and metadata.
        """
        if not os.path.exists(filepath):
            logger.error("File doesn't exist: %s." % filepath)
            return None
        logger.debug("Creates blob '{}'@[{}]".format(blob_name, container_name))
        blob = self.block_blob_service.create_blob_from_path(
            container_name, blob_name, filepath)
        return blob


    def upload(self, container_name, blob_pairs, overwrite=False):
        """
        Uploads files to the container on Azure. Note that 'blob_name' uploaded
        will be converted to posix-style names, which means sep for path is
        '/'.

        `blob_pairs`
            A tuple consists of 2 elements, blob_name and its filepath on local
            filesystem.
        """

        if not self.block_blob_service.exists(container_name):
            logger.info(
                "Container [%s] which upload to doesn't exist, "
                "creating now." % container_name)
            self.create_container(container_name, set_public=True)

        blobs = []
        blobs_in_container = self.list_blobs(container_name)
        for blob_name, filepath in progressbar.progressbar(\
                                    blob_pairs, widgets=self.widgets):
            posix_blob_name = ppath(blob_name)
            if overwrite or (posix_blob_name not in blobs_in_container):
                self.create_blob_from_path(
                    container_name, posix_blob_name, filepath)
                blobs.append(posix_blob_name)

        logger.info("Uploaded %d files to [%s]." % (len(blobs), container_name))
        return blobs


    def get_blob_to_path(self, container_name, blob_name, filepath):
        """
        Gets a blob from the container. The filepath would be returned if gotten
        successfully.
        """
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            logger.debug("Directory '%s' does not exist, creating now..." % dirpath)
            os.makedirs(dirpath)

        # TODO: changes filepath to local-filesystem
        logger.debug("Gets blob '{}' from [{}]".format(blob_name, container_name))
        blob = self.block_blob_service.get_blob_to_path(
            container_name, blob_name, filepath)
        return blob


    def download(self, container_name, dest, blob_names=None):
        """
        Get blobs from the container to the `dest` directory.
        """
        blobs = []

        if not self.block_blob_service.exists(container_name):
            logger.error("Container [%s] does not exist, aborted." % container_name)
            return blobs
        # Get the list of blobs and then do comparision would be much more efficient
        blobs_in_container = self.list_blobs(container_name)

        # Get all blobs if blob_names was not specified
        if not blob_names:
            blob_names = blobs_in_container

        for blob_name in progressbar.progressbar(\
                            blob_names, widgets=self.widgets):
            if ppath(blob_name) in blobs_in_container:
                dest_filepath = normpath(safe_join(dest, blob_name))
                # TODO: not sure posix-style path works for files on container
                # are windows-style
                self.get_blob_to_path(container_name, ppath(blob_name), dest_filepath)
                logger.debug("Got blob '{}' to '{}'.".format(blob_name, dest_filepath))
                blobs.append(blob_name)
            else:
                logger.warning("Blob name '{}' specified does not exist.".format(blob_name))

        return blobs


    def get_blob_to_text(self, container_name, blob_name):
        pass


    def get_blobs(self, container_name, blob_names=None):
        pass


    def set_container_acl(self, container_name, set_public=True):
        """
        Set container access permission to Public.
        """
        if set_public:
            logger.info("Set public read access to container [%s]." % container_name)
            public_access = PublicAccess.Container
        else:
            logger.info("Set public read access to blobs on [%s]." % container_name)
            public_access = PublicAccess.Blob

        self.block_blob_service.set_container_acl(container_name, public_access=public_access)


    def delete_blobs(self, container_name, blob_names):
        """
        Removes blobs from the container.
        """
        blobs = []
        for blob_name in blob_names:
            try:
                blob = self.block_blob_service.delete_blob(container_name, blob_name)
                logger.info(
                    "Delete the blob '%s' from container [%s]." % (blob_name, container_name))
                blobs.append(blob)
            except AzureMissingResourceHttpError as e:
                logger.warning(
                    "The sepcified blob '%s' on [%s] does not exist." % (blob_name, container_name))

        return blobs


    def copy_blobs(self, blob_names, container_name, src_container=None, pattern=None):
        """
        Copy blobs listed in `blob_names` to the dest container.

        `src_container`
            if src_container was given, blob_names are OK to be relative path
            to the container, and will be extended to `http://self.host/src_container/blob_name`

        `pattern`
            if src_container and pattern was given and blob_names was None,
            copies blobs in the src_container meanwhile matches the pattern to
            dest container.

        """
        if blob_names == None:
            if src_container:
                blobs_in_container = self.list_blobs(src_container)
                matchfn = get_matchfn(pattern, True)
                # gets blobs from the src_container which matches the pattern(with ignorecase)
                blob_names = filter(lambda x: matchfn(x), blobs_in_container)
            else:
                raise ImproperlyConfigured(
                    "Method `copy_blobs` is ought to be called with "
                    "`src_container` given if blob_names was set to None."
                    )

        if src_container:
            urls = []
            for blob_name in blob_names:
                # not absolute url path
                if not blob_name.startswith('http'):
                    # extends with the account and container
                    blob_name = "http://{}/{}/{}".format(self.host, src_container, blob_name)
                urls.append(escape_uri_path(blob_name))
            blob_names = urls

        blobs = []
        logger.info("Will copy {} blobs to [{}].".format(len(blob_names), container_name))
        for copy_source in progressbar.progressbar(blob_names, widgets=self.widgets):
            r = re.match(self.blob_pattern, copy_source)
            if r:
                blob_name = r.group(3)
            else:
                logger.error("Blob name specified must be a url: '{}'.".format(copy_source))
                continue

            self.block_blob_service.copy_blob(container_name, \
                                            blob_name, copy_source)
            logger.debug("Copied '{}' to '{}'.".format(copy_source, blob_name))
            blobs.append(blob_name)

        return blobs

    def copy_container(self, src_container, dst_container, pattern=None):
        """
        Copies blobs in `src_container` meanwhile match the `pattern`.
        """
        # creates container if not exists
        self.create_container(dst_container, set_public=True)
        logger.info("Copy blobs from [{}] to [{}]".format(src_container, dst_container))
        self.copy_blobs(None, dst_container,src_container=src_container,pattern=pattern)
