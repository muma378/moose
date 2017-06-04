# -*- coding: utf-8 -*-
import os
import time
import shutil
import unittest
import subprocess

from mock import Mock

from moose.conf import settings
from moose.apps import AppConfig
from moose.core.configs.config import  ConfigLoader
from moose.core.configs.registry import configs, get_conf_cache, get_conf_dirname
from moose.core.exceptions import DoesNotExist, ImproperlyConfigured

settings.configure()

class TestApp1Config(AppConfig):
	verbose_name = u'测试1'
	path = 'tests/sample_data/configs/testapp1'

class TestApp2Config(AppConfig):
	verbose_name = u'测试2'
	path =  'tests/sample_data/configs/testapp2'


class ConfigsRegistryTestCase(unittest.TestCase):
	def setUp(self):
		# Test-App-1
		self.testapp1 = TestApp1Config('testapp1', 'tests.sample_data.configs.testapp1')
		if os.path.exists(get_conf_cache(self.testapp1)):
			os.remove(get_conf_cache(self.testapp1))
		# Test-App-2
		self.testapp2 = TestApp2Config('testapp2', 'tests.sample_data.configs.testapp2')
		if os.path.exists(get_conf_cache(self.testapp2)):
			os.remove(get_conf_cache(self.testapp2))

	def tearDown(self):
		configs.configs_of_app = {}

	def test_get_or_create(self):
		# no values declared in configs_of_app
		self.assertFalse(configs.configs_of_app)

		# basic function test
		testapp1_configs = configs.get_or_create(self.testapp1)
		# 2 configs file in total for app testapp1
		self.assertEqual(len(testapp1_configs._configs), 2)
		# gets the instance parsed from sample1.cfg
		testapp1_sample1_loader = testapp1_configs._configs['sample1.cfg']
		self.assertTrue(isinstance(testapp1_sample1_loader, ConfigLoader))
		testapp1_sample1_config = testapp1_sample1_loader.parse()
		self.assertEqual(testapp1_sample1_config.upload['task_id'], 1)

		# tests if no new instance was declared
		testapp1_configs_copy = configs.get_or_create(self.testapp1)
		self.assertIs(testapp1_configs, testapp1_configs_copy)

		# tests if cache file was updated after creating a new one
		# clears the memory at first
		configs.configs_of_app = {}
		# changes the last modification time for sample2.cfg
		sample2_conf_path = os.path.join(get_conf_dirname(self.testapp1), 'sample2.cfg')
		time.sleep(1)
		subprocess.check_call('touch %s' % sample2_conf_path, shell=True)

		config_cache = get_conf_cache(self.testapp1)
		cache_stat_before = os.stat(config_cache)
		testapp1_configs_new = configs.get_or_create(self.testapp1)
		cache_stat_after = os.stat(config_cache)
		self.assertNotEqual(cache_stat_before.st_mtime, cache_stat_after.st_mtime, "Configs cache is not synchronized.")

	def test_synchronize(self):
		testapp1_configs = configs.get_or_create(self.testapp1)

		self.assertFalse(testapp1_configs.find_by_name('sample3.cfg'))
		sample3_conf_path = os.path.join(get_conf_dirname(self.testapp1), 'sample3.cfg')
		# appends the new config `sample3.cfg`
		shutil.copy(testapp1_configs.find_by_name('sample2.cfg').config_path, sample3_conf_path)
		testapp1_configs.synchronize()
		self.assertTrue(testapp1_configs.find_by_name('sample3.cfg'))

		# deletes the config file `sample3.cfg`
		os.remove(sample3_conf_path)
		testapp1_configs.synchronize()
		self.assertFalse(testapp1_configs.find_by_name('sample3.cfg'))

	def test_find_by_attr(self):
		testapp1_configs = configs.get_or_create(self.testapp1)
		sample1_config = testapp1_configs.find_by_attr('upload', 'task_id', 1)
		self.assertEqual(sample1_config.common['name'], 'sample-test1')

		sample2_config = testapp1_configs.find_by_attr('upload', 'task_id', 2)
		self.assertEqual(sample2_config.common['name'], 'sample-test2')
