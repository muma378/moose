import os
import pickle

from moose.apps import AppConfig
from moose.core.exceptions import ImproperlyConfigured
from moose.conf import settings

from .loader import ConfigLoader
from .writer import ConfigWriter


class ConfigsRegistry(object):
	"""
	Manages all configs for an app, it loads and dumps relevant information.
	"""
	configs_of_app = {}

	def __init__(self, app_config, all_configs=None):
		self.app_config = app_config

		# Mapping of config names to ConfigLoader instances for the app_config
		if all_configs:
			self._configs = all_configs
		else:
			self._configs = {}

			# Called after initializing self.app_config and self._configs
			self.synchronize()

		self.template_conf = self.get_default_template()

	def get_default_template(self):
		config_template_path = self.app_config.config_template
		if not os.path.exists(config_template_path):
			raise ImproperlyConfigured("Config template path '%s' does not exist." % config_template_path)

		return ConfigWriter(config_template_path)

	def append(self, config_name):
		if not isinstance(self.template_conf, ConfigWriter):
			raise ImproperlyConfigured(
				"Member of the class 'template_conf' must "
				"be an instance of 'ConfigWriter'")

		config_path = os.path.join(self.app_config.configs_dirname, config_name)
		self.template_conf.write(config_path)


	# Updates self._configs for the case that configs created, modified or deleted
	def synchronize(self):
		conf_dirname = get_conf_dirname(self.app_config)
		# get all config files
		config_files = list(filter(lambda x: x.endswith(settings.CONFIG_EXTENSION), os.listdir(conf_dirname)))

		# a flag to indicates if any config was parsed at this time
		anyone_changed = False

		# updates the modified and appended
		for config_name in config_files:
			config_file = os.path.join(conf_dirname, config_name)
			self._configs[config_name], is_changed = ConfigLoader.create(config_file, self._configs)
			# Ture if any changed
			anyone_changed = anyone_changed or is_changed

		# removes the deleted
		to_delete = []
		for config_name in self._configs.keys():
			if config_name not in config_files:
				to_delete.append(config_name)

		# dictionary is not allowed to change size in py3
		for config_name in to_delete:
			del self._configs[config_name]
			anyone_changed = True

		return anyone_changed

	# find the config_loader with a given path to the config
	def find_by_path(self, config_path):
		return self.find_by_name(os.path.basename(config_path))

	# find the config_loader with a given config name
	def find_by_name(self, config_name):
		return self._configs.get(config_name)

	def __clear(self):
		# pop instead of del
		self.configs_of_app.pop(self.app_config.label)
		cache_path = get_conf_cache(self.app_config)
		if os.path.exists(cache_path):
			os.remove(cache_path)

	@classmethod
	def get_or_create(cls, installed_app):
		# finds the AppConfig according to the app_label
		if not isinstance(installed_app, AppConfig):
			raise ImproperlyConfigured("'%s' isn't instance of AppConfig." % installed_app)

		# Step 1. checks if it was loaded in the memory recently
		# TODO: synchronize here or not?
		if cls.configs_of_app.get(installed_app.label):
			return cls.configs_of_app[installed_app.label]

		# finds the directory path of config for the app
		conf_dirname = get_conf_dirname(installed_app)
		conf_cache_file = get_conf_cache(installed_app)

		# app_signature = cls.get_signature(installed_app)
		# Step 2. try to load it from the pickle
		tuned = False
		if os.path.exists(conf_cache_file):
			with open(conf_cache_file, 'rb') as f:
				try:
					all_configs = pickle.load(f)
					configs = cls(installed_app, all_configs)
				except EOFError as e:
					configs = cls(installed_app)
					tuned = True
				else:
					# checks that any config was changed, appended or deleted
					# if there was, loads it with ConfigLoader
					tuned = configs.synchronize()
		else:
			# Step 3. creates configs from top to bottom
			configs = cls(installed_app)
			tuned = True
			# configs.signature = app_signature

		# Content was changed since the last dumping
		if tuned:
			with open(conf_cache_file, 'wb') as f:
				pickle.dump(configs._configs, f)

		# Saves it to the memory
		cls.configs_of_app[installed_app.label] = configs
		return configs

	# checks the config files status every times, reloads if mtime was inconsistent
	@classmethod
	def get_signature(cls, app_config):
		return None

	def find_by_tag(self, tag):
		raise NotImplementedError

	def find_by_attr(self, section, option, val):
		for config_name, config_loader in self._configs.items():
			config = config_loader.parse()
			if getattr(config, section):
				if getattr(config, section).get(option) == val:
					return config_loader
		return None

	def find(self, conf_desc):
		raise NotImplementedError


# TODO: moves to AppConfig for an attribute
def get_conf_dirname(app_config):
	return os.path.join(app_config.path, settings.CONFIGS_DIRNAME)

def get_conf_cache(app_config):
	return os.path.join(app_config.path, settings.CONFIGS_DIRNAME,  settings.CONFIG_CACHE_NAME)

def find_nearest_conf(app_config):
	"""
	returns the path of newly-created config file for the app.
	"""
	return None

# finds the matched config with a given conf_desc
# specifying the desc when running in command-line, for example:
# name or path: `-c config-file-name` or `-c config-file-path`
# tag: `-c t:tag-name`
# attribute: `-c a:attr=val`
def find_matched_conf(app_config, conf_desc):
	# instantiates a ConfigsRegistry with a given app_config
	configs = ConfigsRegistry.get_or_create(app_config)

	if conf_desc.find(settings.CONFIG_DESC_EXPR_SEP) == 1:
		# separated by colon, consists of a letter and an expression
		style, _, expr = conf_desc.partition(settings.CONFIG_DESC_EXPR_SEP)
		if style == settings.CONFIG_DISCOVER_BY_TAG:
			# t:tag-name
			config_loader = configs.find_by_tag(expr)
		elif style == settings.CONFIG_DISCOVER_BY_ATTR:
			# a:attr=val
			attr, _, val = expr.partition(settings.CONFIG_DESC_ATTR_VAL_SEP)
			section, _, option = attr.partition(settings.CONFIG_DESC_SECT_OPT_SEP)
			config_loader = configs.find_by_attr(section, option, val)
		else:
			return None
	else:
		# it would be a path if is could be addressed
		if os.path.exists(conf_desc):
			config_loader = configs.find_by_path(conf_desc)
		else:
			# is it a name?
			config_loader = configs.find_by_name(conf_desc)

	return config_loader
