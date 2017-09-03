# classes to send mails to users
# author: xiao yang <xiaoyang0117@gmail.com>
# date: 2016.Oct.31

# TODO: exceptions handlers, sending mails with attachments

import smtplib
from email.mime.text import MIMEText
from moose.conf import settings


class BaseMailSender(object):
	"""sends mails with text only"""
	def __init__(self, smtphost=None, smtpport=None, smtpuser=None, smtppass=None):
		super(BaseMailSender, self).__init__()
		self.smtphost = smtphost
		self.smtpport = smtpport
		self.smtpuser = smtpuser
		self.smtppass = smtppass

		self.smtp = smtplib.SMTP(self.smtphost, self.smtpport)
		# logger.info("connected to smtp server {0}".format(self.smtphost))

	def __del__(self):
		self.smtp.quit()

	def send(self, from_addr, to_addrs, subject, content):
		msg = MIMEText(content)

		msg['Subject'] = subject
		msg['From'] = from_addr
		msg['To'] = to_addrs
		self.smtp.sendmail(from_addr, to_addrs, msg.as_string())


class NotifyMailSender(BaseMailSender):
	"""notifies users if tasks was done"""
	subject_template = None
	content_template = None

	def __init__(self, recipients):
		host = settings.MAIL_SETTINGS['smtp_server']
		port = settings.MAIL_SETTINGS['smtp_port']
		sender = settings.MAIL_SETTINGS['sender']
		super(NotifyMailSender, self).__init__(smtphost=host, smtpport=port)
		self.recipients = ', '.join(recipients)
		self.sender = sender

	def notify(self, context):
		self.send(
			self.sender, self.recipients,
			self.subject_template.format(**context),
			self.content_template.format(**context),
		)
