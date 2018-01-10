# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from moose.apps import AppConfig


class TrialConfig(AppConfig):
    name = 'trial'
    verbose_name = u"试标项目"

    def ready(self):
        self.register('Upload', 'upload')
        self.register('UploadDirs', 'upload_dirs')
        self.register('Export', 'export')
        self.register('DrawAndExport', 'draw')
