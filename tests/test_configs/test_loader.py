import unittest

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
		pass

	def test_utf8_codec(self):
		pass

	def test_utf8_bom_codec(self):
		pass

	def test_gbk_codec(self):
		pass

	def test_parse(self):
		loader = ConfigLoader(self.test_config_path)
		test_config = loader.parse()

		self.assertTrue(isinstance(test_config, Config))
		self.assertEqual(test_config.common['name'], 'sample-test')
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

	def test_string_opt(self):
		opt = OptionParser('test', 'string')
		self.assertEqual(opt.get_value(), 'test')

	def test_sequence_opt(self):
		opt = OptionParser('a, b,c,  d, ', 'list')
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
