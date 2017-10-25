# -*- coding: utf-8 -*-
import os
import codecs
import ConfigParser

import chardet

from moose.utils._os import npath
from moose.utils.datautils import stripl
from moose.core.exceptions import DoesNotExist, ImproperlyConfigured
from moose.conf import settings


class Config(object):
	"""
	An instance built and returned by ConfigLoader. It has bare attribute and
	method to minimize conflict between attributes defined by classes and
	sections defined in configs.
	"""
	pass


class ConfigLoader(object):
	"""
	Class to parse a config file, it loads extra info for the config file each
	time but parses the config file only at the first time and saves them in a
	cache.
	If the `mtime` was not changed, it would not do the parsing again.
	"""
	def __init__(self, conf_path):
		if not os.path.exists(conf_path):
			raise DoesNotExist("Config path does not exist: '%s'." % npath(conf_path))

		self.path = conf_path
		# checks and updates the codecs of config file if necessary
		# which must be done before setting attribute mtime.
		self.__update_codec()

		# Reference to the Argvs registry that holds this ArgvConfig.
		self._config = self._parse()

		# gets posix stat result at last
		config_stat = os.stat(conf_path)
		# time of last access/modification/file-status-change
		self.atime = config_stat.st_atime
		self.mtime = config_stat.st_mtime
		self.ctime = config_stat.st_ctime


	@classmethod
	def create(cls, conf_path, configs):
		# Checks if it was loaded from the cache
		argv_config = configs.get(conf_path)
		is_newly_created = True

		if argv_config:
			# get the posix stat for the config file
			config_stat = os.stat(conf_path)
			# checks if the content was changed since last parsing
			if argv_config.mtime == config_stat.st_mtime:
				return argv_config, not is_newly_created

		# create a new ArgvConfig instance
		return cls(conf_path), is_newly_created

	def __update_codec(self):
		# character encoding detect
		with open(self.path, 'r+') as f:
			overwrite = False
			content = f.read()
			result = chardet.detect(content)
			if not result:
				raise ImproperlyConfigured(
					"Unknown encoding for '%s'." % self.path)

			# coding with utf-N-BOM, removes the BOM signs '\xff\xfe' or '\xfe\xff'
			if content.startswith(codecs.BOM_LE) or content.startswith(codecs.BOM_BE):
				content = content[2:]
				overwrite = True	# flag to rewrite the config file

			file_encoding = result['encoding']
			# coding with other codecs except for ascii or utf-8
			if file_encoding!='ascii' and file_encoding!=settings.FILE_CHARSET:
				try:
					content = content.decode(file_encoding).encode(settings.FILE_CHARSET)
					overwrite = True
				except UnicodeDecodeError as e:
					raise ImproperlyConfigured(
						"Unknown encoding for '%s'." % self.path)
				except UnicodeEncodeError as e:
					raise ImproperlyConfigured(
						"Unrecognized symbols in '%s'." % self.path)
			# erases the content and rewrites with 'utf-8' encoding
			if overwrite:
				f.truncate(0)	# truncate the config size to 0
				f.seek(0)	# rewind
				f.write(content)


	def _parse(self):
		# A wrapper to parse config files
		config_parser = ConfigParser.ConfigParser()
		config_parser.read(self.path)

		# TODO: a more clear format of config
		# Config always starts with a [meta] section, which lists the following
		# sections to use in the option `keys`
		sections_str = config_parser.get(settings.CONFIG_META_KEYWORD,
			settings.CONFIG_KEYS_KEYWORD)
		sections = stripl(sections_str.split(settings.CONFIG_LIST_SEP))

		# init a config instance, it contains the fields in file only
		config = Config()
		section_parser = SectionParser(config_parser)
		for section in sections:
			setattr(config, section, section_parser.parse(section))

		return config


	def parse(self):
		return self._config



class SectionParser(object):
	"""
	Class to parse a section in config files.

	A section consists of `body` and `meta`, while body represents values for
	options and meta indicates types. They are usually presented as below:

	```
	[meta_section]
	opt = type

	[section]
	opt = value
	```
	"""

	def __init__(self, config_parser):
		self._config_parser = config_parser

	def get_meta_key(self, section_name):
		return ''.join((settings.CONFIG_META_KEYWORD,
			settings.CONFIG_META_SECTION_CONCATE,
			section_name))

	def parse_meta(self, section_name):
		# Some sections have meta data in the form of [meta_section-name],
		# which describes the type for a key
		section_meta_key = self.get_meta_key(section_name)

		# indicates types of options for the section
		type_hints = {}
		if self._config_parser.has_section(section_meta_key):
			type_hints = {k:v for k, v in self._config_parser.items(section_meta_key)}

		return type_hints

	def parse(self, section_name):
		# tests if the section was existed
		if not self._config_parser.has_section(section_name):
			raise ImproperlyConfigured("No section: '%s'." % section_name)

		# parses meta at first
		type_hints = self.parse_meta(section_name)

		options = {}

		# begin to parse the section body
		for opt, val in self._config_parser.items(section_name):
			options[opt] = OptionParser(val, type_hints.get(opt)).get_value()

		return options


class OptionBaseType(object):
	def __init__(self, val):
		self.value = val

	def get_value(self):
		raise NotImplementedError


class OptionUnicode(OptionBaseType):
	"""
	Type for unicode or option not specified. (decoded in __update_codec)
	"""
	opt_code = (None, 'unicode', 'Unicode')
	default_charset = 'utf-8'

	def get_value(self):
		return self.value.decode(self.default_charset)


class OptionString(OptionBaseType):
	"""
	Type for string.
	"""
	opt_code = ('string', 'String')

	def get_value(self):
		return str(self.value)


class OptionSequence(OptionBaseType):
	opt_code = ('list', 'sequence', 'List', 'Sequence')

	def get_value(self):
		# splited by a sep such as ','
		return tuple(stripl(self.value.split(settings.CONFIG_LIST_SEP)))

class OptionInteger(OptionBaseType):
	opt_code = ('int', 'Integer')

	def get_value(self):
		return int(self.value)

class OptionFloat(OptionBaseType):
	opt_code = ('float', 'Float', 'double', 'Double')

	def get_value(self):
		return float(self.value)

class OptionRange(OptionBaseType):
	"""
	Type for continuous numbers, represented as `start-end`.

	Noted that differs from the builtin function range, it is full closed, which
	equals to range(start, end+1)
	"""
	opt_code = ('range', 'Range')

	def get_value(self):
		if self.value.find(settings.CONFIG_RANGE_SEP) == -1:
			raise ImproperlyConfigured("Format of range is incorrect.")
		start, end = stripl(self.value.split(settings.CONFIG_RANGE_SEP))
		return range(int(start), int(end)+1)

class OptionParser(object):
	option_types = (
		OptionUnicode,
		OptionString,
		OptionSequence,
		OptionInteger,
		OptionFloat,
		OptionRange
		)

	def __init__(self, val, option_code=None):
		self.value = val
		self.set_option_code(option_code)

	def set_option_code(self, option_code):
		for opt_type_klass in self.option_types:
			if option_code in opt_type_klass.opt_code:
				self._option = opt_type_klass(self.value)
				return
		# TODO: lists all supported option code
		raise ImproperlyConfigured("Does not support option type %s." % option_code)

	def get_value(self):
		return self._option.get_value()
