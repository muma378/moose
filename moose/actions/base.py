# -*- coding: utf-8 -*-
import abc
import threading

class IllegalAction(Exception):
	"""action was halted somehow"""
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


class MixinAction(threading.Thread):
	"""
	A mixin class to provide the object extra ability.
	"""
	pass
