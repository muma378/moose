# -*- coding: utf-8 -*-
class BaseException(Exception):
	def __init__(self, msg):
		super(BaseException, self).__init__()
		self.msg = msg


class ArgumentsError(BaseException):
	def __init__(self, msg='invalid arguments passed in'):
		super(ArgumentsError, self).__init__(msg)

class ConnTimeoutError(BaseException):
	def __init__(self, msg='connection timeout'):
		super(ConnTimeoutError, self).__init__(msg)

class ImproperlyConfigured(Exception):
    """moose is somehow improperly configured"""
    pass

class AppRegistryNotReady(Exception):
    """The moose.apps registry is not populated yet"""
    pass

class DoesNotExist(Exception):
	"""File specified does not exist"""
	pass

class SuspiciousOperation(Exception):
    """The user did something suspicious"""

class SuspiciousFileOperation(SuspiciousOperation):
    """A Suspicious filesystem operation was attempted"""
    pass
