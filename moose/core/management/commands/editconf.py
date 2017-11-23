# -*- coding: utf-8 -*-
import subprocess

from moose.apps import apps
from moose.core.management.base import ConfigsCommand, CommandError
from moose.conf import settings

class Command(ConfigsCommand):

    help = (
        "Open a text editor with a config file loaded, settings.EDITOR defines "
        "the application to use, which is 'vim' on *nix and 'notepad' on "
        "Windows by default."
        )
    editor = settings.EDITOR

    # TODO: edits the config file with arguments, no need to open an editor
    # replaces the option with a value specified in the command line.
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

    def handle_config_loader(self, app_config, config_loader, **options):
        subprocess.check_call([self.editor, config_loader.path])
