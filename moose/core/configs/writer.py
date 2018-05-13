# -*- coding: utf-8 -*-
import os

from moose.utils._os import npath
from moose.utils.six.moves import configparser
from moose.core.exceptions import DoesNotExist, ImproperlyConfigured


class ConfigWriter(object):
	"""
	Class to write a config file, it loads the template config, sections and
	options are allowed to added and modified, then writes to a local file.
	"""
	def __init__(self, template_path):
		if not os.path.exists(template_path):
			raise ImproperlyConfigured("Config path '%s' does not exist." % npath(template_path))

		self.template_path = template_path
		self._config = self.__load_template()

	def __load_template(self):
		config = configparser.RawConfigParser()
		config.read(self.template_path)
		return config

	def add_section(self, section_name):
		self._config.add_section(section_name)

	def set(self, section_name, option_name, value):
		self._config.set(section_name, option_name, value)

	def write(self, conf_path):
		if os.path.exists(conf_path):
			raise ImproperlyConfigured("Config path '%s' exists already." % conf_path)

		with open(conf_path, 'w') as configfile:
			self._config.write(configfile)
