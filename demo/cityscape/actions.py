# -*- coding: utf-8 -*-
from moose import actions

class Upload(actions.AbstractAction):
    def run(self, **kwargs):
        config = kwargs.get('config')
        return "upload files in '%s'" % config.common['root']


class Export(actions.AbstractAction):
    def run(self, **kwargs):
        return "export"
