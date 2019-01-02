# -*- coding: utf-8 -*-
import unittest
import io
import os
import codecs
import mock

from moose.conf import settings
from moose.utils import encoding
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
		self.test_config_path = "tests/test_configs/data/sample.conf"
		with open(self.test_config_path, "rb") as f:
			self.test_content = f.read()

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

		with mock.patch("moose.core.configs.loader.os") as mock_os:
			mock_os.stat.return_value = mock.MagicMock(mtime=1546416606)
			loaded_config, newly_created = \
				ConfigLoader.create(self.test_config_path, configs)
			self.assertTrue(newly_created)
			self.assertNotEqual(new_config, loaded_config)

		# Passed a not existed file
		with self.assertRaises(DoesNotExist) as context:
			ConfigLoader.create('does/not/existed/path.conf', configs)

	def test_codecs(self):
		config_content = self.test_content.decode('utf-8')
		loader = ConfigLoader(self.test_config_path)
		mock_module = "moose.core.configs.loader.open"

		def test_data_untouched(read_data):
			with mock.patch(mock_module, mock.mock_open(read_data=read_data)) as mock_open:
				loader._update_codec("")
				mock_fd = mock_open()
				# not rewrite if encoded with UTF-8
				mock_fd.write.assert_not_called()

		# Test with empty and UTF-8 encoded data
		test_data_untouched("")
		test_data_untouched(config_content.encode('utf-8'))

		def test_data_rewritten(read_data, write_data):
			with mock.patch(mock_module, mock.mock_open(read_data=read_data)) as mock_open:
				loader._update_codec("")
				mock_fd = mock_open()
				# rewrite for encoded with UTF-8-SIG
				mock_fd.write.assert_called_with(write_data)

		# Test with normal encoded data
		test_data_rewritten(config_content.encode('utf-8-sig'), self.test_content)
		test_data_rewritten(config_content.encode('utf-16'), self.test_content)
		test_data_rewritten(config_content.encode('utf-32'), self.test_content)
		test_data_rewritten(config_content.encode('gbk'), self.test_content)

		# Test with too short content
		short_data = u"短testcase"
		test_data_untouched(short_data.encode('utf-8'))
		with self.assertRaises(ImproperlyConfigured):
			# with confidence too low
			test_data_rewritten(short_data.encode('gbk'), short_data.encode('utf-8'))

		# Test with invalid encoding detected
		japanese_data = u"通常、関数やメソッドが単体テストの単位（ユニット）となります。 プログラムが全体として正しく動作しているかを検証する結合テストは、開発の比較的後の段階でQAチームなどによって行なわれることが多いのとは対照的に、単体テストは、コード作成時などの早い段階で開発者によって実施されることが多いのが特徴です"
		test_data_rewritten(japanese_data.encode('shift_jis'), japanese_data.encode('utf-8'))
		with mock.patch("moose.core.configs.loader.chardet") as mock_chardet:
			mock_chardet.detect.return_value = {"encoding": "utf-8", "confidence": 1}
			with self.assertRaises(ImproperlyConfigured):
				# with same encoding as FILE_CHARSET
				test_data_rewritten(japanese_data.encode('gbk'), japanese_data.encode('utf-8'))

			mock_chardet.detect.return_value = {"encoding": "johab", "confidence": 1}
			with self.assertRaises(ImproperlyConfigured):
				# with incorrect encoding reported
				test_data_rewritten(japanese_data.encode('gbk'), japanese_data.encode('utf-8'))


	def test_parse(self):
		loader = ConfigLoader(self.test_config_path)
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
