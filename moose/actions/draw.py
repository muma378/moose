# -*- coding: utf-8 -*-
import os

from moose.process import image

from .base import AbstractAction, IllegalAction

import logging
logger = logging.getLogger(__name__)

class BasePainter(AbstractAction)
    """
    Class to simulate the action of drawing shapes on pictures,

    """
    data_model = ''

    def get_context(self, kwargs):
        raise NotImplementedError

    def fetch(self, context):
        raise NotImplementedError

    def run(self, **kwargs):
        context = self.get_context(kwargs)
        queryset = self.fetch(context)
        output = []
        neffective = 0
        data_model_cls = import_string(self.data_model)
        for item in queryset:
            dm = data_model_cls(item)
            if dm.is_effective():
                neffective += 1
                self.handle(dm, context)

        output.append("%d results processed." % neffective)
        return '\n'.join(output)
