# -*- coding: utf-8 -*-
import inspect
import time
from datetime import datetime

from pytz import timezone

from moose.conf import settings

class CommandRecord(object):
	"""
	Keeps a record for each command, including the command name,
	options and the full command user typed.
	It will records the launch and end time automatically, and
	display as user defined.
	"""

	datetime_format = "%c"
	# datetime_format = "%d/%m/%y, %H:%M:%S"
	display_format = (
		"[{r.app_label} - {r.command_name}] ({r.launch_time} ~ {r.running_time})"
		" \"{r.message}\""
		)

	def __init__(self, app_config, command, message):
		self.id = str(int(time.time()*1000))
		self.app_config = app_config
		self.command = command
		self.message = message
		# start to time when initializing
		self._launch_time = datetime.now()
		self._ending_time = None

	def __str__(self):
		# members = inspect.getmembers(self)
		# context = {k[0]: k[1] for k in members}
		# return self.display_format.format(**context)
		return self.display_format.format(r=self)

	@property
	def app_label(self):
		return self.app_config.label

	@property
	def command_name(self):
		return self.command.name

	@property
	def launch_time(self):
		loc_tz = timezone(settings.TIME_ZONE)
		return loc_tz.localize(self._launch_time).strftime(self.datetime_format)

	@property
	def running_time(self):
		if self._ending_time:
			return str(self._ending_time-self._launch_time)
		else:
			return '?'

	def done(self):
		self._ending_time = datetime.now()
