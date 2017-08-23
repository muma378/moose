# -*- coding: utf-8 -*-

from moose.apps import apps
from moose.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
	help = (
		"Run an app with a specified config, the latest one by default."	
		)