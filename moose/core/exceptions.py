# -*- coding: utf-8 -*-

class ConnectionTimeout(Exception):
    """Time out for a connections"""
    pass

class DatabaseError(Exception):
    """"""
    pass

class ImproperlyConfigured(Exception):
    """Moose is somehow improperly configured"""
    pass

class AppRegistryNotReady(Exception):
    """The moose.apps registry is not populated yet"""
    pass

class DoesNotExist(Exception):
    """File specified does not exist"""
    pass

class SuspiciousOperation(Exception):
    """The user did something suspicious"""
    pass

class SuspiciousFileOperation(SuspiciousOperation):
    """A Suspicious filesystem operation was attempted"""
    pass
