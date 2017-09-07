# -*- coding: utf-8 -*-
import os
import subprocess
from datetime import datetime

from moose.apps import apps
from moose.core.management.base import AppCommand, CommandError
from moose.core.configs.registry import ConfigsRegistry
from moose.conf import settings

class Command(AppCommand):

    help = (
        "Generate a config file for the application according to the template. "
        "settings.EDITOR defines "
        "the utility to use, which is 'vim' on *nix and 'notepad' on "
        "Windows by default."
        )

    editor = settings.EDITOR
    datetime_format = '%b%d-%H%M'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        # TODO: add argument -a to customise the config to generate
        parser.add_argument(
            '-c', '--config', metavar='config_name', action='append',
            help='Specify a config name for the newly created.',
        )
        parser.add_argument(
            '-q', '--quite', action='store_true',
            help='Do not pops the editor after the config created.'
        )


    def handle_app_config(self, app_config, **options):
        keep_quite = options.pop('quite')
        config_names = options.pop('config')

        configs = ConfigsRegistry.get_or_create(app_config)

        if not config_names:
            config_names = [self.name_in_datetime(), ]

        output = []
        for config_name in config_names:
            if not config_name.endswith(settings.CONFIG_EXTENSION):
                config_name += settings.CONFIG_EXTENSION
            configs.append(config_name)

            config_path = os.path.join(app_config.configs_dirname, config_name)
            if not keep_quite:
                if self.editor == 'vim':
                    self.open_vim(config_path)
                else:
                    subprocess.check_call([self.editor, config_path])

            output.append("Config file '%s' for '%s' is created." % (config_name, app_config.label))

        return "\n".join(output)


    def name_in_datetime(self):
        return datetime.now().strftime(self.datetime_format)

    def open_vim(self, filepath):
        """
        Execute `/?` after loading the file, which makes it jumps to
        the next occurence of `?` when 'n' was pressed.
        """
        subprocess.check_call(['vim', '-c "set nu"', '-c "/?"', filepath])
