# -*- coding: utf-8 -*-
import unittest
import io
import os
import codecs

from moose.conf import settings
from moose.utils.six.moves import configparser
from moose.core.configs.loader import \
	Config, ConfigLoader, OptionParser, SectionParser
from moose.core.exceptions import DoesNotExist, ImproperlyConfigured


class ConfigLoaderTestCase(unittest.TestCase):
	"""
	> sample_data/configs/sample.conf:
	[meta]
	keys = common,upload,export

	[common]
	name = sample-test
	root = /path/to/data

	[meta_upload]
	task_name = list
	task_id = int

	[upload]
	task_name = a,b,c,d
	task_id = 1

	[meta_export]
	task_id = range

	[export]
	task_id = 100-103
	"""

	def setUp(self):
		self.test_config_path = "tests/sample_data/configs/sample.conf"

	def test_create(self):
		# The first time to meet the config
		configs = {}
		new_config, newly_created = \
			ConfigLoader.create(self.test_config_path, configs)
		self.assertTrue(newly_created)

		# At the second time
		configs[self.test_config_path] = new_config
		loaded_config, newly_created = \
			ConfigLoader.create(self.test_config_path, configs)
		self.assertFalse(newly_created)
		self.assertEqual(new_config, loaded_config)

		# Passed a not existed file
		with self.assertRaises(DoesNotExist) as context:
			ConfigLoader.create('does/not/existed/path.conf', configs)


	def test_utf8_codec(self):
		self.__test_parse(self.test_config_path)

	def test_utf8_bom_codec(self):
		with io.open(self.test_config_path, encoding='utf-8') as f:
			conf_str = f.read()
		filename, _ = os.path.splitext(self.test_config_path)
		bom_conf_path = filename+'_bom.conf'
		with open(bom_conf_path, 'wb') as f:
			conf_bom_str = codecs.BOM + conf_str.encode('utf-8')
			f.write(conf_bom_str)
		self.__test_parse(bom_conf_path)

	def test_gbk_codec(self):
		with io.open(self.test_config_path, encoding='utf-8') as f:
			conf_str = f.read()
		filename, _ = os.path.splitext(self.test_config_path)
		gbk_conf_path = filename+'_gbk.conf'
		with open(gbk_conf_path, 'wb') as f:
			conf_gbk_str = conf_str.encode('gbk')
			f.write(conf_gbk_str)
		self.__test_parse(gbk_conf_path)

	def test_short_codec(self):
		"""The content is too short to get the codecs"""

		with self.assertRaises(ImproperlyConfigured) as context:
			self.__test_parse("tests/sample_data/configs/sample_short.conf")

	def __test_parse(self, test_config_path):
		loader = ConfigLoader(test_config_path)
		test_config = loader.parse()

		self.assertTrue(isinstance(test_config, Config))
		self.assertEqual(test_config.common['name'], u"测试样例")
		self.assertEqual(test_config.upload['task_name'], ('a', 'b', 'c', 'd'))
		self.assertEqual(test_config.upload['task_id'], 1)
		self.assertSequenceEqual(test_config.export['task_id'], [100, 101, 102, 103])

		self.assertEqual(test_config.export['task_id'][0] , 100)
		self.assertEqual(test_config.export['task_id'][1] , 101)
		self.assertEqual(test_config.export['task_id'][-1] , 103)

class SectionParserTestCase(unittest.TestCase):
	def setUp(self):
		config_parser = configparser.ConfigParser()
		config_parser.read("tests/sample_data/configs/sample.conf")
		self.section_parser = SectionParser(config_parser)

	def test_get_meta_key(self):
		self.assertEqual(self.section_parser.get_meta_key('common'), 'meta_common')

	def test_parse_meta(self):
		# tests section without meta
		type_hints = self.section_parser.parse_meta('common')
		self.assertEqual(type_hints, {})

		# tests section with meta
		type_hints = self.section_parser.parse_meta('upload')
		self.assertEqual(type_hints, {'task_name': 'list', 'task_id': 'int'})

	def test_parse(self):
		upload_section = self.section_parser.parse('upload')
		self.assertEqual(upload_section, {'task_name': ('a', 'b', 'c', 'd'), 'task_id': 1})

		# tests a section not existed
		with self.assertRaises(ImproperlyConfigured):
			self.section_parser.parse('not_existed')


class OptionParserTestCase(unittest.TestCase):

	def test_default_opt(self):
		opt = OptionParser('test')
		self.assertEqual(opt.get_value(), 'test')

	def test_float_opt(self):
		opt = OptionParser('123.4', 'float')
		self.assertEqual(opt.get_value(), 123.4)

	def test_string_opt(self):
		opt = OptionParser('test', 'string')
		self.assertEqual(opt.get_value(), 'test')

	def test_sequence_opt(self):
		opt = OptionParser('a, b,c,  d, ', 'list')
		self.assertEqual(opt.get_value(), ('a', 'b', 'c', 'd'))

		opt = OptionParser('a, b,c,  d, ', 'sequence')
		self.assertEqual(opt.get_value(), ('a', 'b', 'c', 'd'))

		opt_solo = OptionParser('a', 'list')
		self.assertEqual(opt_solo.get_value(), ('a', ))

	def test_range_opt(self):
		opt = OptionParser('100-103', 'range')
		self.assertSequenceEqual(opt.get_value(), [100, 101, 102, 103])

		opt_error = OptionParser('123', 'range')
		with self.assertRaises(ImproperlyConfigured):
			opt_error.get_value()

	def test_undefined_opt(self):
		# tests initializion with undefined type
		with self.assertRaises(ImproperlyConfigured):
			opt = OptionParser('abc', 'undefined')

if __name__ == "__main__":
    unittest.main()
