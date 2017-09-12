# -*- coding: utf-8 -*-
import time
import logging
from moose import actions
from moose.connection.cloud import azure

logger = logging.getLogger('moose.actions')

class Upload(actions.AbstractAction):
    def run(self, **kwargs):
        config = kwargs.get('config')
        time.sleep(2)
        logger.info("upload files in '%s'" % config.common['root'])
        return "upload files in '%s'" % config.common['root']


class Export(actions.AbstractAction):
    def run(self, **kwargs):
        return "export"
