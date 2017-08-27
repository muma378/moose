# -*- coding: utf-8 -*-
from moose import actions

class Upload(actions.AbstractAction):
    def run(self, **kwargs):
        return "upload"


class Export(actions.AbstractAction):
    def run(self, **kwargs):
        return "export"
