from __future__ import unicode_literals


VERSION = (0, 9, 5, 'Beta', 0)

def get_version(version=None):
    return '0.9.5Beta'

__version__ = get_version(VERSION)


def setup(set_prefix=True):
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the app registry.
    Set the thread-local urlresolvers script prefix if `set_prefix` is True.
    """
    from moose.apps import apps
    from moose.conf import settings

    from moose.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)

    # apps.populate(settings.INSTALLED_APPS)
