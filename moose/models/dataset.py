# -*- coding: utf-8 -*-
import os
from datetime import datetime
from moose.process.image import common

class Dataset(object):
    """
    Dataset is a class to gather relative items into
    a group.
    """
    data_model = None
    def __init__(self, queryset, context):
        self.queryset = queryset
        self.context = context
        self.models = []
        for item in queryset:
            self.models.append(self.data_model(item))


class MScocoDataset(Dataset):

    @property
    def info(self):
        return {
            'year': 2017,
            'version': '0.1',
            'description': 'Trial of Annotation on Cityscape',
            'contributor': 'DATATANG',
            'url': '',
            'date_created': datetime.today()
        }

    @property
    def images(self):
        images = []
        counter = self.context['nimage']
        src = self.context['root']
        for model in self.models:
            counter += 1
            setattr(model, 'id', counter)

            w, h = common.image_size(os.path.join(src, model.filepath))
            images.append({
                'id': counter,
                'width': w,
                'height': h,
                'file_name': model.filename,
                'url': model.filepath,
                'date_captured': None
                })
        self.context['nimage'] = counter
        return images

    @property
    def annotations(self):
        annotations = []
        counter = self.context['nannotation']
        for model in self.models:
            for annotation in model.segmentations:
                counter += 1
                annotations.append({
                    'id': counter,
                    'image_id': model.id,
                    'category_id': self.get_category_id(annotation['category']),
                    'segmentation': annotation['segmentation'],
                    'area': -1.0,
                    'bbox': annotation['bbox'],
                    'iscrowd': annotation['iscrowd'],
                })
        self.context['nannotation'] = counter
        return annotations

    def get_category_id(self, name):
        raise NotImplementedError

    @property
    def categories(self):
        raise NotImplementedError

    @property
    def data(self):
        return {
            'info': self.info,
            'images': self.images,
            'annotations': self.annotations,
            'license': []
        }
