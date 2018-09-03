# -*- coding: utf-8 -*-

from . import BaseModel
from . import fields

class AudioModel(BaseModel):
    """
    @template: 多段落语音标注v2.1
    """
    url         = fields.SourceMappingField(prop_name='url')
    clips       = fields.SourceMappingField(prop_name='urlList')
    mark_result = fields.ResultMappingField(prop_name='markResult')

    @property
    def filepath(self):
        return self.url

    @property
    def segments(self):
        for segment in self.mark_result:
            yield segment['start'], segment['end'], segment['extend']
