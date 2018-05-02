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

	1. Get Environment
		Converts options in *.cfg file to a dict named `environment`.
		At this stage, you can keep arguments will be used in the
		following steps and throw away ones won't.

	2. Schedule
		Splits and assembles the keys in `environment` to generate
		a `context` as the argument to be called in the near future.
		An `environment` may implicitly ask for a job done with
		different context. At this stage, you are able to control how
		they flow and the order to be handled.

	3. Handle
		Handles the job with the context provided above. Each handle()
		should returns a `string` representing the result.
	"""

	def get_environment(self, kwargs):
		raise NotImplementedError('subclasses of BaseAction must provide a get_environment()')

	def schedule(self, environment):
		raise NotImplementedError('subclasses of BaseAction must provide a schedule()')

	def handle(self, context):
		raise NotImplementedError('subclasses of BaseAction must provide a handle()')

	def run(self, **kwargs):
		environment = self.get_environment(kwargs)
		output = []
		for context in self.schedule(environment):
			output.append(self.handle(context))
		return '\n'.join(output)

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
