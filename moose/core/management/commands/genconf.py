# -*- coding: utf-8 -*-
import subprocess

from moose.apps import apps
from moose.core.management.base import ConfigsCommand, CommandError
from moose.core.configs.registry import find_matched_conf
from moose.conf import settings

class Command(ConfigsCommand):

    help = (
        "Generate a config file for the application according to the template. "
        "settings.EDITOR defines "
        "the utility to use, which is 'vim' on *nix and 'notepad' on "
        "Windows by default."
        )

    editor = settings.EDITOR


    def handle_config_loader(self, app_config, config_loader, **options):

        subprocess.check_call([self.editor, config_loader.path])
