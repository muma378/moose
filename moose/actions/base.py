# -*- coding: utf-8 -*-
import abc
import sys
# TODO: Defines actions work in multithreading
# import threading

from moose.core.management.color import color_style
from moose.core.management.base import OutputWrapper
from moose.core.exceptions import ImproperlyConfigured
from moose.utils.module_loading import import_string

class IllegalAction(Exception):
	"""Action was halted somehow"""
	pass

class InvalidConfig(Exception):
	"""Configs are not set as the requirement"""
	pass

class QueryError(Exception):
	"""Failed to query data with given arguments"""
	pass

class AbstractAction:
	"""
	A base class of action.

	Actions are abstract to operations handled in processing data. such as
	uploading files to azure, dumping data from database and etc.

	"""
	__metaclass__ = abc.ABCMeta

	@abc.abstractmethod
	def run(self, **kwargs):
		raise NotImplementedError


class BaseAction(AbstractAction):
	"""
	A standard base action is splited into 4 steps:

	1. Parse
		Converts options in *.cfg file to a dict named `environment`.
		At this stage, you can keep arguments will be used in the
		following steps and throw away ones won't.

	2. Schedule
		Splits and assembles the keys in `environment` to generate
		a `context` as the argument to be called in the near future.
		An `environment` may implicitly ask for a job done with
		different context. At this stage, you are able to control how
		they flow and the order to be handled.

	3. Execute
		Handles the job with context provided above. Each execute()
		should return a `string` representing the output.

	4. Teardown
		Handles the rest works after executing all context.
	"""

	stats_dump = True
	stats_class = 'moose.actions.stats.StatsCollector'

	def __init__(self, app_config, stdout=None, stderr=None, style=None):
		super(BaseAction, self).__init__()

		# Sets app_config
		self.app = app_config

		# Sets stdout and stderr, which were supposed to passed from command
		self.stdout = stdout or sys.stdout
		self.stderr = stderr or sys.stderr
		self.style  = style or color_style()

		# Imports stats class
		self.stats = import_string(self.stats_class)(self)

		# String to record and display after all works done
		self.output = []

	def parse(self, kwargs):
		raise NotImplementedError('subclasses of BaseAction must provide a `parse()`')

	def schedule(self, environment):
		raise NotImplementedError('subclasses of BaseAction must provide a `schedule()`')

	def execute(self, context):
		raise NotImplementedError('subclasses of BaseAction must provide a `handle()`')

	def teardown(self, env):
		pass

	def run(self, **kwargs):
		environment = self.parse(kwargs)
		for context in self.schedule(environment):
			stats_id = self.execute(context)
			self.stats.close_action(self, stats_id)
		self.teardown(environment)
		return '\n'.join(self.output)


class SimpleAction(BaseAction):
	"""
	Provides entry points for concrete actions. This is more like a
	contract-oriented programming: declares interfaces that subclasses call
	but descendant classes define.
	In this way, actions are able to abstract common features in subclasses
	meanwhile implement the custom functions in subclasses of subclass.
	"""
	def get_config(self, kwargs):
		if kwargs.get('config'):
			config = kwargs.get('config')
		else:
			logger.error("Missing argument: 'config'.")
			raise IllegalAction(
				"Missing argument: 'config'. This error is not supposed to happen, "
				"if the action class was called not in command-line, please provide "
				"the argument `config = config_loader._parse()`.")
		return config

	def set_environment(self, env, config, kwargs):
		"""
		Entry point for concrete actions to add custom environment,
		called at the end of `parse()`.
		"""
		pass

	def set_context(self, context, i):
		"""
		Entry point for concrete actions to add custom context,
		called at the end of `schedule()`.
		"""
		pass

	def terminate(self, context):
		"""
		Entry point for concrete actions to terminate the execution.
		called at the end of `execute()`.
		"""
		pass

	def get_stats_id(self, context):
		return ''


	def getseq(self, list_or_ele):
		"""
		Returns a list always, converts to a list with an element if it was not.
		"""
		return list_or_ele if isinstance(list_or_ele, list) or isinstance(list_or_ele, tuple) else [list_or_ele, ]

	def assert_equal_size(self, *lists):
		"""
		Raises an error if any one of the list does not has the equal size.
		"""
		lsize = len(lists[0])
		for l in lists:
			if len(l) != lsize:
				raise InvalidConfig("List wiht unequal length found in config.")
