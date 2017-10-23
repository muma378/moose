import sys
import threading
import warnings
from collections import Counter, OrderedDict, defaultdict
from functools import partial

from moose.core.exceptions import AppRegistryNotReady, ImproperlyConfigured
from moose.utils import lru_cache

from .config import AppConfig

class Apps(object):
	"""
	A registry that stores the configuration of installed applications.

	It also keeps track of models eg. to provide reverse-relations.
	"""

	def __init__(self, installed_apps=()):
		# installed_apps is set to None when creating the master registry
		# because it cannot be populated at that point. Other registries must
		# provide a list of installed apps and are populated immediately.
		if installed_apps is None and hasattr(sys.modules[__name__], 'apps'):
			raise RuntimeError("You must supply an installed_apps argument.")

		# Mapping of app labels => model names => model classes. Every time a
		# model is imported, ModelBase.__new__ calls apps.register_model which
		# creates an entry in all_models. All imported models are registered,
		# regardless of whether they're defined in an installed application
		# and whether the registry has been populated. Since it isn't possible
		# to reimport a module safely (it could reexecute initialization code)
		# all_models is never overridden or reset.
		self.all_actions = defaultdict(OrderedDict)

		# Mapping of labels to AppConfig instances for installed apps.
		self.app_configs = OrderedDict()

		# Stack of app_configs. Used to store the current state in
		# set_available_apps and set_installed_apps.
		self.stored_app_configs = []

		# Whether the registry is populated.
		# self.apps_ready = False
		# self.ready = False

		# Lock for thread-safe population.
		self._lock = threading.Lock()

		# Maps ("app_label", "modelname") tuples to lists of functions to be
		# called when the corresponding model is ready. Used by this class's
		# `lazy_model_operation()` and `do_pending_operations()` methods.
		self._pending_operations = defaultdict(list)

	def populate(self, installed_apps=None):
		"""
		Loads application configurations and models.

		This method imports each application module and then each model module.

		It is thread safe and idempotent, but not reentrant.
		"""
		# if self.ready:
		#     return

		# populate() might be called by two threads in parallel on servers
		# that create threads before initializing the WSGI callable.
		with self._lock:
			# ALLOWED TO REENTRANT NOE
			# if self.ready:
			#     return

			# app_config should be pristine, otherwise the code below won't
			# guarantee that the order matches the order in INSTALLED_APPS.
			# if self.app_configs:
			#     raise RuntimeError("populate() isn't reentrant")


			# Phase 1: initialize app configs and import app modules.
			for entry in installed_apps:
				if isinstance(entry, AppConfig):
					app_config = entry
				else:
					app_config = AppConfig.create(entry)
				if app_config.label in self.app_configs:
					raise ImproperlyConfigured(
						"Application labels aren't unique, "
						"duplicates: %s" % app_config.label)

				self.app_configs[app_config.label] = app_config
				app_config.apps = self

			#  for duplicate app names.
			counts = Counter(
				app_config.name for app_config in self.app_configs.values())
			duplicates = [
				name for name, count in counts.most_common() if count > 1]
			if duplicates:
				raise ImproperlyConfigured(
					"Application names aren't unique, "
					"duplicates: %s" % ", ".join(duplicates))

			# self.apps_ready = True

			# Phase 2: import models modules.
			for app_config in self.app_configs.values():
				try:
					app_config.import_actions()
				except ImportError as e:
					raise ImproperlyConfigured(e.message)

			# self.actions_ready = True

			# Phase 3: run ready() methods of app configs.
			for app_config in self.get_app_configs():
				app_config.ready()

			# self.ready = True

	def get_app_configs(self):
		return self.app_configs.values()

	def get_app_config(self, app_label):
		# TODO: it is not necessary to load all apps every time
		try:
			return self.app_configs[app_label]
		except KeyError as e:
			try:
				# populate the app if not found in attribute `app_configs`
				self.populate(installed_apps=[app_label])
				return self.app_configs[app_label]
			except ImportError:
				message = "No installed app with label '%s'." % app_label
				for app_config in self.get_app_configs():
					if app_config.name == app_label:
						message += " Did you mean '%s'?" % app_config.label
						break
				raise LookupError(message)


apps = Apps(installed_apps=None)
