# classes to send mails to users
# author: xiao yang <xiaoyang0117@gmail.com>
# date: 2016.Oct.31

# TODO: exceptions handlers, sending mails with attachments

import smtplib
from email.mime.text import MIMEText
from moose.conf import settings


class BaseMailSender(object):
	"""sends mails with text only"""
	def __init__(self, host=None, port=None, user=None, password=None):
		super(BaseMailSender, self).__init__()
		self.host = host if host else settings.EMAIL_HOST
		self.port = port if port else settings.EMAIL_PORT
		self.user = user if user else settings.EMAIL_HOST_USER
		self.password = password if password else settings.EMAIL_HOST_PASSWORD

		# initialize the connection to smtp server
		self.smtp = smtplib.SMTP(self.host, self.port)
		# logger.info("connected to smtp server {0}".format(self.host))

	def __del__(self):
		self.smtp.quit()

	def send(self, from_addr, to_addrs, subject, content):
		msg = MIMEText(content)

		msg['Subject'] = subject
		msg['From'] = from_addr
		msg['To'] = to_addrs
		self.smtp.sendmail(from_addr, to_addrs, msg.as_string())


class BaseTemplateMail(BaseMailSender):
	"""
	Sends mails to recipients with rendering templates declared in the
	derived classes. Except for templates for subject and content, derived
	classes must also provide a dict `context` contains variables in templates.
	"""
	subject_template = None
	content_template = None

	def __init__(self, recipients):
		super(BaseTemplateMail, self).__init__()
		self.recipients = ', '.join(recipients)
		self.sender = settings.DEFAULT_FROM_EMAIL

	def send(self, context):
		super(BaseTemplateMail, self).send(
			self.sender, self.recipients,
			self.subject_template.format(**context),
			self.content_template.format(**context),
			)
