# -*- coding: utf-8 -*-
import logging

from moose.connection.cloud import AzureBlobService
from moose.shortcuts import ivisit

from . import AbstractAction, IllegalAction

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

    `route`
        Generates an index file.

    """
    def parse(self, config):
        pass

    def explore(self, context):
        pass

    def schedule(self, files, context):
        pass

    def upload(self, group, context):
        pass

    def route(self, blobs, context):
        pass

    def run(self, **kwargs):
        config = kwargs.get('config')

        if config:
            context = self.parse(config)
        else:
            logger.error()
            raise IllegalAction("Missing argument: config.")

        files = self.explore(context)

        for group in self.schedule(files, context):
            blobs = self.upload(group, context)
            self.route(blobs, context)
