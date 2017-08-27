# -*- coding: utf-8 -*-
# common.connection.azure -
import os
import sys
import Queue

from azure.storage.blob import BlockBlobService, PublicAccess
from azure.common import AzureConflictHttpError, AzureMissingResourceHttpError

from moose.utils._os import npath
from moose.shortcuts import ivisit
from moose.conf.settings import logger
from moose.conf.settings import AZURE_SETTINGS as az, CONNECTION_SETTINGS as cs
# from service.progressbar import ProgressBar
# from service.progressbar import widgets


class AzureBlob(object):
	"""Connection to azure blob service."""
	def __init__(self, account=az["account"], key=az["key"], endpoint_suffix=az['endpoint_suffix'],
			timeout=cs['timeout'], workers=az['workers'], chunks=az['chunks']):
		self.account = account
		self.key = key
		self.endpoint_suffix = endpoint_suffix
		self.timeout = timeout
		self.host = account + '.blob.' + endpoint_suffix
		self.workers = workers
		self.chunks = chunks
		logger.info("initialize azure blob service with account {0} and endpoint_suffix {1}".format(
			self.account, self.endpoint_suffix))
		# diffs from database, it sends a request when required
		self.block_blob_service = BlockBlobService(
			account_name=self.account, account_key=self.key, endpoint_suffix=self.endpoint_suffix)

	def create_container(self, container_name, public=False):
		logger.info("creating a container {0} on {1}".format(container_name, self.host))

		if public:
			public_access = PublicAccess.Container
			logger.info("setting container {0} public".format(container_name))
		else:
			public_access = None

		try:
			result = self.block_blob_service.create_container(container_name,
				fail_on_exist=True, timeout=self.timeout , public_access=public_access)
		except AzureConflictHttpError as e:
			logger.error("the specified container {0} already exists".format(container_name))
			result = False

		if result:
			logger.info("succeed")
		else:
			logger.error("failed to create the container {0} on {1}".format(container_name, self.host))
		return result


	def list_containers(self, prefix=None, suffix=''):
		container_names = []
		logger.info("request to list containers on {0}".format(self.host))
		results = self.block_blob_service.list_containers(prefix=prefix, timeout=self.timeout)
		for container_name in results:
			if container_name.endswith(suffix):
				container_names.append(container_name)

		logger.info("{0} containers found on {1}".format(len(container_names), self.host))
		return container_names


	def list_blobs(self, container_name, prefix=None, suffix=''):
		blob_names = []
		logger.info("request to list blobs in container {0}@{1}".format(container_name, self.host))

		try:
			results = self.block_blob_service.list_blobs(container_name, prefix=prefix, timeout=self.timeout)
		except AzureMissingResourceHttpError as e:
			logger.error("the specified container {0} does not exist".format(container_name))
			results = []

		for blob in results:
			if blob.name.endswith(suffix):
				blob_names.append(blob.name)

		logger.info("{0} blobs found in {1}".format(len(blob_names), self.host))
		return blob_names


	def upload(self, container_name, root_path, suffix='', prefix=''):
		self.create_container(container_name)

		logger.info("begin to upload {0} to container - {1} hosted in {2}: ".format(
			root_path, container_name, self.host))

		for filepath, blob_name in ivisit(root_path, '', pattern=suffix):
			if prefix and not os.path.basename(blob_name).startswith(prefix):
				continue
			blob_name = os.path.normcase(blob_name)
			self.create_blob_from_path(container_name, blob_name, filepath)


	def create_blob_from_path(self, container_name, blob_name, filepath):
		logger.info("{0} => {1}@{2}".format(npath(filepath), npath(blob_name), container_name))
		sys.stdout.write("uploading {0} ... ".format(npath(blob_name)))
		sys.stdout.flush()

		def progress_callback(current, total):
			if total > self.block_blob_service.MAX_SINGLE_PUT_SIZE \
				and current%(self.chunk*self.block_blob_service.MAX_BLOCK_SIZE)  == 0:
				print("{0:.1f} of {1:.2f} MB ({2:.1%}) uploaded".format(current/1048576.0, total/1048576.0, 1.0*current/total))

		self.block_blob_service.create_blob_from_path(container_name,
			blob_name, filepath, progress_callback=progress_callback)
		print("done")


	def download(self, container_name, root_path, suffix='', prefix=None):
		blob_list = self.list_blobs(container_name, suffix=suffix, prefix=prefix)

		for blob_name in blob_list:
			filepath = os.path.join(root_path, os.path.normpath(blob_name))
			if os.path.exists(filepath):
				logger.info("{0}@{1} existed already, skipped".format(blob_name, container_name))
			else:
				self.get_blob_to_path(container_name, blob_name, filepath)

	def get_blob_to_path(self, container_name, blob_name, filepath):
		logger.info("{0}@{1} => {2}".format(blob_name, container_name, filepath))
		sys.stdout.write("downloading {0} ... ".format(blob_name))
		sys.stdout.flush()
		# blob = self.block_blob_service.get_blob_properties(container_name, blob_name)
		# _widgets = [blob_name+': ', widgets.Percentage(), ' ', widgets.Bar(marker='='),
#              ' ', widgets.ETA(), ' ', widgets.FileTransferSpeed()]
		# pbar = ProgressBar(widgets=_widgets, maxval=blob.properties.content_length).start()


		def progress_callback(current, total):
			if total > self.block_blob_service.MAX_SINGLE_GET_SIZE \
				and current%(self.chunk*self.block_blob_service.MAX_CHUNK_GET_SIZE):
				print("{0:.1f} of {1:.2f} MB ({2:.1%}) downloaded".format(current/1048576.0, total/1048576.0, 1.0*current/total))
			# pbar.update(current)

		if not os.path.exists(os.path.dirname(filepath)):
			os.makedirs(os.path.dirname(filepath))

		self.block_blob_service.get_blob_to_path(
			container_name, blob_name, filepath, progress_callback=progress_callback)
		# pbar.finish()
		print("done")


	def set_container_acl(self, container_name, public=True):
		if public:
			logger.info("setting full public read access for container {0} and its blob data".format(container_name))
			public_access = PublicAccess.Container
		else:
			logger.info("setting public read access for blobs in container {0} ".format(container_name))
			public_access = PublicAccess.Blob

		self.block_blob_service.set_container_acl(container_name, public_access=public_access)


	def delete_blob(self, container_name, blob_names):
		failed = []
		for blob_name in blob_names:
			try:
				self.block_blob_service.delete_blob(container_name, blob_name)
				logger.info("deleted blob data {0} from container {1}".format(blob_name, container_name))
			except AzureMissingResourceHttpError as e:
				failed.append(blob_name)
				logger.warning("the sepcified blob {0}@{1} does not exist".format(blob_name, container_name))
		return failed

	def move(self, src_container, dst_conta):
		pass
