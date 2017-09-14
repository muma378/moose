# -*- coding: utf-8 -*-
class AbstractMappingField(object):

	def get_val(self):
		raise NotImplementedError

class CommonMappingField(AbstractMappingField):

	def __init__(self, dict_name, prop_name, default=None):
		self.dict_name = dict_name
		self.prop_name = prop_name
		self.default   = default

	def get_val(self, anno):
		return anno[self.dict_name].get(self.prop_name, self.default)

class SourceMappingField(CommonMappingField):

	dict_name = 'source'

	def __init__(self, prop_name, default=None):
		super(SourceMappingField, self).__init__(self.dict_name, prop_name, default)

class ResultMappingField(CommonMappingField):

	dict_name = 'result'

	def __init__(self, prop_name, default=None):
		super(ResultMappingField, self).__init__(self.dict_name, prop_name, default)

class LambdaMappingField(AbstractMappingField):

	def __init__(self, lambda_fn):
		self.lambda_fn = lambda_fn

	def get_val(self, anno):
		return self.lambda_fn(anno)
