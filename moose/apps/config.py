import os
from importlib import import_module

from moose.core.exceptions import ImproperlyConfigured
from moose.utils._os import upath
from moose.utils import six
from moose.utils.module_loading import module_has_submodule
from moose.conf import settings

ACTIONS_MODULE_NAME = 'actions'
CONFIGS_DIRNAME = 'configs'
CONFIGS_CACHE_NAME = '.config'
DATA_DIRNAME = 'data'

class AppConfig(object):
	"""
	Class representing a Moose application and its configuration.
	"""

	def __init__(self, app_name, app_module):
		# Full Python path to the application eg. 'django.contrib.admin'.
		self.name = app_name

		# Root module for the application eg. <module 'django.contrib.admin'
		# from 'django/contrib/admin/__init__.pyc'>.
		self.module = app_module

		# Reference to the Apps registry that holds this AppConfig. Set by the
		# registry when it registers the AppConfig instance.
		self.apps = None

		# The following attributes could be defined at the class level in a
		# subclass, hence the test-and-set pattern.

		# Last component of the Python path to the application eg. 'admin'.
		# This value must be unique across a Moose project.
		if not hasattr(self, 'label'):
			self.label = app_name.rpartition(".")[2]

		# Human-readable name for the application eg. "Admin".
		if not hasattr(self, 'verbose_name'):
			self.verbose_name = self.label.title()

		# Filesystem path to the application directory eg.
		# u'/usr/lib/python2.7/dist-packages/django/contrib/admin'. Unicode on
		# Python 2 and a str on Python 3.
		if not hasattr(self, 'path'):
			self.path = self._path_from_module(app_module)

		# table to store the map between alias and actions
		self.alias_action_table = {}

		# Filesystem path to the config directory of the application.
		if not hasattr(self, 'configs_dirname'):
			self.configs_dirname = os.path.join(self.path, CONFIGS_DIRNAME)

		# Filesystem path to the config cache file.
		if not hasattr(self, 'configs_cache_path'):
			self.configs_cache_path = os.path.join(self.configs_dirname, CONFIGS_CACHE_NAME)

		# Filesystem path to the template of the config file.
		if not hasattr(self, 'config_template'):
			self.config_template = os.path.join(self.path, settings.CONF_TEMPLATE_NAME)

		if not hasattr(self, 'data_dirname'):
			self.data_dirname = os.path.join(self.path, DATA_DIRNAME)

	def __repr__(self):
		return '<%s: %s>' % (self.__class__.__name__, self.label)

	def _path_from_module(self, module):
		"""Attempt to determine app's filesystem path from its module."""
		# See #21874 for extended discussion of the behavior of this method in
		# various cases.
		# Convert paths to list because Python 3's _NamespacePath does not
		# support indexing.
		paths = list(getattr(module, '__path__', []))
		if len(paths) != 1:
			filename = getattr(module, '__file__', None)
			if filename is not None:
				paths = [os.path.dirname(filename)]
			else:
				# For unknown reasons, sometimes the list returned by __path__
				# contains duplicates that must be removed (#25246).
				paths = list(set(paths))
		if len(paths) > 1:
			raise ImproperlyConfigured(
				"The app module %r has multiple filesystem locations (%r); "
				"you must configure this app with an AppConfig subclass "
				"with a 'path' class attribute." % (module, paths))
		elif not paths:
			raise ImproperlyConfigured(
				"The app module %r has no filesystem location, "
				"you must configure this app with an AppConfig subclass "
				"with a 'path' class attribute." % (module,))
		return upath(paths[0])


	@classmethod
	def create(cls, entry):
		"""
		Factory that creates an app config from an entry in INSTALLED_APPS.
		"""
		try:
			# If import_module succeeds, entry is a path to an app module,
			# which may specify an app config class with default_app_config.
			# Otherwise, entry is a path to an app config class or an error.
			module = import_module(entry)

		except ImportError:
			# Track that importing as an app module failed. If importing as an
			# app config class fails too, we'll trigger the ImportError again.
			module = None

			mod_path, _, cls_name = entry.rpartition('.')

			# Raise the original exception when entry cannot be a path to an
			# app config class.
			if not mod_path:
				raise

		else:
			# TODO: rename entry from 'mscoco' to 'mscoco.apps.MscocoConfig'
			# renames the directory 'apps' to 'app'
			try:
				# If this works, the app module specifies an app config class.
				entry = module.default_app_config
			except AttributeError:
				# Otherwise, it simply uses the default app config class.
				return cls(entry, module)
			else:
				mod_path, _, cls_name = entry.rpartition('.')

		# If we're reaching this point, we must attempt to load the app config
		# class located at <mod_path>.<cls_name>
		mod = import_module(mod_path)
		try:
			cls = getattr(mod, cls_name)
		except AttributeError:
			if module is None:
				# If importing as an app module failed, that error probably
				# contains the most informative traceback. Trigger it again.
				import_module(entry)
			else:
				raise

		# Check for obvious errors. (This check prevents duck typing, but
		# it could be removed if it became a problem in practice.)
		if not issubclass(cls, AppConfig):
			raise ImproperlyConfigured(
				"'%s' isn't a subclass of AppConfig." % entry)

		# Obtain app name here rather than in AppClass.__init__ to keep
		# all error checking for entries in INSTALLED_APPS in one place.
		try:
			app_name = cls.name
		except AttributeError:
			raise ImproperlyConfigured(
				"'%s' must supply a name attribute." % entry)

		# Ensure app_name points to a valid module.
		try:
			app_module = import_module(app_name)
		except ImportError:
			raise ImproperlyConfigured(
				"Cannot import '%s'. Check that '%s.%s.name' is correct." % (
					app_name, mod_path, cls_name,
				)
			)

		# Entry is a path to an app config class.
		return cls(app_name, app_module)

	def comment(self):
		return ''

	def import_models(self):
		# Dictionary of models for this app, primarily maintained in the
		# 'all_models' attribute of the Apps this AppConfig is attached to.
		# self.models = self.apps.all_models[self.label]

		# if module_has_submodule(self.module, MODELS_MODULE_NAME):
		#     models_module_name = '%s.%s' % (self.name, MODELS_MODULE_NAME)
		#     self.models_module = import_module(models_module_name)
		pass

	def import_actions(self):
		# Dictionary of actions for this app, primarily maintained in the
		# 'all_actions' attribute of the Apps this AppConfig is attached to.
		# self.actions = self.apps.all_actions[self.label]
		if module_has_submodule(self.module, ACTIONS_MODULE_NAME):
			actions_module_name = '%s.%s' % (self.name, ACTIONS_MODULE_NAME)
			self.actions_module = import_module(actions_module_name)


	def ready(self):
		"""
		Override this method in subclasses to run code when Moose starts.
		"""
		pass

	def register(self, action_klass, alias, default=False, entry=None):
		"""
		To store the map between actions and names, which would be called by
		the sub-command 'run' and option '-a'
		"""
		if self.alias_action_table.get(alias):
			raise ImproperlyConfigured("Action alias '%s' was registered." % alias)

		# TODO: take into account argument default and entry
		self.alias_action_table[alias] = getattr(self.actions_module, action_klass)

	def get_action_klass(self, action_alias):
		return self.alias_action_table.get(action_alias)


	# TODO: returns a list containing all actions allowed
	def list_actions(self):
		return []
