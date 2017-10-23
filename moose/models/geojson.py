# -*- coding: utf-8 -*-

from . import BaseModel
from . import fields

class GeoJSONModel(BaseModel):
	mark_result = fields.ResultMappingField(prop_name='markResult')

	@property
	def icoordinates(self):
		for geometry, _ in self.ifeatures:
			yield geometry['coordinates']

	@property
	def ifeatures(self):
		if isinstance(self.mark_result, dict) and self.mark_result.get('features'):
			for feature in self.mark_result['features']:
				yield feature['geometry'], feature['properties']
