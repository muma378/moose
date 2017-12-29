# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from moose import models

class BodyProfileModel(models.GeoJSONModel):
    """
    @template_name: 人体图像多边形标注V2.1
    """
    @property
    def filepath(self):
        return self.source['url']

    @property
    def data(self):
        segmentations = []
        for geometry, properties in self.ifeatures:
            segmentations.append({
                'body': geometry['coordinates'],
            })
        return segmentations

    @property
    def datalist(self):
        datalist = []
        for segmentation in self.data:
            for label, polygons in segmentation.items():
                for polygon in polygons:
                    datalist.append((label, polygon))
        return datalist
