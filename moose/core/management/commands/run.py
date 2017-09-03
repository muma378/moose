# -*- coding: utf-8 -*-

from moose.apps import apps
from moose.core.management.base import AppCommand, CommandError
from moose.core.configs.registry import find_matched_conf
from moose.core.records import CommandRecord, records
from moose.core.mail import NotifyMailSender


class CommandRunNotifier(NotifyMailSender):
	subject_template = "[moose] {r.app_label} - {c.action_alias}"
	content_template = (
		"Task '{r.id}' you started is finised, here is the information:\n"
		"\t\"{r}\"\n\n"
		"Output of the action is:\n"
		"\t\"{output}\""
		)

	def get_context(self, record, command, output):
		return {
			'r': record,
			'c': command,
			'output': output,
		}
		

class Command(AppCommand):
	help = (
		"Run an app with a specified config, the latest one by default."
		)

	def add_arguments(self, parser):
		super(Command, self).add_arguments(parser)

		parser.add_argument(
			'-a', '--action',
			help='Specify an action to perform, registered at \'apps.py\' before.',
		)
		parser.add_argument(
			'-c', '--config', action='append', dest='configs',
			help='Names of configs to be run with, uses the latest one by default.',
		)
		parser.add_argument(
			'-m', '--message', action='store',
			help='Execution message, will be appended to records.',
		)
		parser.add_argument(
			'-q', '--quite', action='store_true',
			help='Do not add the execution to records.',
		)
		parser.add_argument(
			'-e', '--email', action='append', dest='recipients',
			help='Sends mails to recipients once the task was done.',
		)

	def handle_app_config(self, app_config, **options):
		self.action_alias = options['action']
		self.configs 	  = options['configs']

		keep_quite	= options['quite']
		recipients	= options['recipients']
		message		= options['message']
		if not message:
			message = self.comment()

		record = CommandRecord(app_config, self, message)

		action_klass = app_config.get_action_klass(self.action_alias)
		if action_klass:
			actor = action_klass(app_config)
		else:
			raise ImproperlyConfigured("Unknown action alias '%s'." % action_alias)

		# run with configs and get the output
		output = []
		for conf_desc in self.configs:
			config = find_matched_conf(app_config, conf_desc)
			output.append(actor.run(config=config))

		# to close the timer
		record.done()
		# print record

		if not keep_quite:
			records.add(record)

		output_str = '\n'.join(output)
		if recipients:
			mail_sender = CommandRunNotifier(recipients)
			context = mail_sender.get_context(record, self, output_str)
			mail_sender.notify(context)

		return output_str

	def comment(self):
		return "run '%s' with <%s>." % (self.action_alias, ','.join(self.configs))
