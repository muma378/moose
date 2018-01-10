# -*- coding: utf-8 -*-
from moose.apps import AppConfig

# from cityscape import actions

class CityscapeConfig(AppConfig):
    name = 'cityscape'
    verbose_name = u"街景道路标注"

    def ready(self):
        self.register('StandardUpload', 'upload', default=True)
        self.register('Export', 'export')
        self.register('PastTasksUpload', 'upload')
