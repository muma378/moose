# -*- coding: utf-8 -*-
import time
from moose import actions

class Upload(actions.AbstractAction):
    def run(self, **kwargs):
        config = kwargs.get('config')
        time.sleep(2)
        return "upload files in '%s'" % config.common['root']


class Export(actions.AbstractAction):
    def run(self, **kwargs):
        return "export"
