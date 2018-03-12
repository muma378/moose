# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from moose import actions
from moose.utils.encoding import smart_text
from moose.process.image import draw
from moose.utils._os import makeparents

from demo import settings

class Upload(actions.upload.SimpleUpload):
    default_pattern = ('*.jpg', '*.png')


class SatellitePicsUpload(Upload):
    """
    @template_name: 卫星图片标注V2.2
    """
    def index(self, blob_pairs, context):
        catalog = []
        for blobname, filename in blob_pairs:
            catalog.append({
                'url': blobname,
            })
        return catalog

class Export(actions.export.SimpleExport):
    data_model = 'trial.models.TrialModel'

class UploadDirs(actions.upload.SimpleUpload):
    default_pattern = ('*.jpg', '*.png')

    def parse(self, config, kwargs):
        return {
            'dirnames': [ smart_text(x) for x in config.upload.get('dirnames', [''])]
        }

    def split(self, all_blob_pairs, context):
        task_ids = context['task_id']
        dirnames = context['dirnames']
        for dirname, task_id in zip(dirnames, task_ids):
            sub_blob_pairs = filter(lambda x: dirname in x[1], all_blob_pairs)
            yield str(task_id), [ (os.path.relpath(x[0], dirname), x[1]) for x in sub_blob_pairs]

class DrawAndExport(actions.export.DownloadAndExport):
    data_model = 'trial.models.BodyProfileModel'

    PALLET = {
        u'body': 255,
    }

    def draw(self, model, context):
        data_dir = os.path.join(self.app.data_dirname, context['title'])
        img_name = os.path.join(data_dir, model.filepath)
        dst_name = os.path.join(data_dir, 'masks', model.filepath)
        makeparents(dst_name)
        draw.draw_polygons(img_name, dst_name, model.datalist, self.PALLET, grayscale=True)

    def handle(self, model, context):
        # super(DrawAndExport, self).handle(model, context)
        self.draw(model, context)
