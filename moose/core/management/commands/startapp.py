# -*- coding: utf-8 -*-
import os
import shutil
from importlib import import_module

from moose.core.management.base import CommandError
from moose.core.management.templates import TemplateCommand
from moose.conf import settings

class Command(TemplateCommand):
    help = (
        "Creates a Moose app directory structure for the given app name in "
        "the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide an application name."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        parser.add_argument('-c', '--config', dest='configfile', default='template',
            help='The template file to use as the default config for the application',
        )

    def handle(self, **options):
        app_name, target = options.pop('name'), options.pop('directory')
        self.validate_name(app_name, "app")

        # Check that the app_name cannot be imported.
        try:
            import_module(app_name)
        except ImportError:
            pass
        else:
            raise CommandError(
                "%r conflicts with the name of an existing Python module and "
                "cannot be used as an app name. Please try another name." % app_name
            )

        super(Command, self).handle('app', app_name, target, **options)

        # copys the config template to the application
        config_template = options.pop('configfile')
        if not config_template.endswith(settings.CONFIG_EXTENSION):
            config_template += settings.CONFIG_EXTENSION

        project_name = os.path.basename(os.getcwd())
        project_template_path = os.path.join(os.getcwd(), project_name, config_template)

        app_template_path = os.path.join(os.getcwd(), app_name, settings.CONF_TEMPLATE_NAME)
        shutil.copyfile(project_template_path, app_template_path)
