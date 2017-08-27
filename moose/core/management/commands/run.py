# -*- coding: utf-8 -*-

from moose.apps import apps
from moose.core.management.base import AppCommand, CommandError


class Command(AppCommand):
	help = (
		"Run an app with a specified config, the latest one by default."
		)

	def add_arguments(self, parser):
		super(Command, self).add_arguments(parser)

		parser.add_argument(
			'-a', '--action',
			help='Specify an action to perform.',
		)
		parser.add_argument(
			'-c', '--config', action='append', dest='configs',
			help='Names of configs to be run with, uses the latest one by default.',
		)

	def handle_app_config(self, app_config, **options):
		action_alias = options['action']
		configs = options['configs']

		result = app_config.run(action_alias, configs)
		return '\n'.join(result)
