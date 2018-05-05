# -*- coding: utf-8 -*-
import abc
import threading

class IllegalAction(Exception):
	"""Action was halted somehow"""
	pass

class InvalidConfig(Exception):
	"""Configs are not set as the requirement"""
	pass

class AbstractAction:
	"""
	A base class of action.

	Actions are abstract to operations handled in processing data. such as
	uploading files to azure, dumping data from database and etc.

	Abstract Factory Pattern(https://en.wikipedia.org/wiki/Abstract_factory_pattern)
	is used in implementing the module.
	"""
	__metaclass__ = abc.ABCMeta

	def __init__(self, app_config):
		self.app = app_config

	@abc.abstractmethod
	def run(self, **kwargs):
		raise NotImplementedError


class BaseAction(AbstractAction):
	"""
	A standard base action is splited into 3 steps:

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
	"""

	def parse(self, kwargs):
		raise NotImplementedError('subclasses of BaseAction must provide a parse()')

	def schedule(self, environment):
		raise NotImplementedError('subclasses of BaseAction must provide a schedule()')

	def execute(self, context):
		raise NotImplementedError('subclasses of BaseAction must provide a handle()')

	def run(self, **kwargs):
		environment = self.parse(kwargs)
		output = []
		for context in self.schedule(environment):
			output.append(self.execute(context))
		return '\n'.join(output)


class SimpleAction(BaseAction):
	"""

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
		Entry point for subclassed commands to add custom environment.
		"""
		pass

	def set_context(self, context, i):
		"""
		Entry point for subclassed commands to add custom context.
		"""
		pass



class BaseStat:
	"""
	An active counter to stash all statistic.
	"""
	pass


class MixinAction(threading.Thread):
	"""
	A mixin class to provide the object extra ability.
	"""
	pass
