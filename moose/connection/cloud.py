# -*- coding: utf-8 -*-
# common.connection.azure -
import os
import sys

from azure.storage.blob import BlockBlobService, PublicAccess
from azure.common import AzureConflictHttpError, AzureMissingResourceHttpError

from moose.utils._os import npath, ppath, safe_join
from moose.conf import settings
from moose.core.exceptions import ImproperlyConfigured
# from moose.conf.settings import logger
# from moose.conf.settings import AZURE_SETTINGS as az, CONNECTION_SETTINGS as cs
# from service.progressbar import ProgressBar
# from service.progressbar import widgets


class AzureBlobService(object):
	"""
	Application interface to access <Azure Blob Storage Service>. A wrapper of
	the module 'BlockBlobService' from azure SDK for python.
	"""
	def __init__(self, settings_dict, stdout, stderr):
		# Set stdout and stderr to colorize the output
		self.stdout = stdout
		self.stderr = stderr

		# Set settings for azure connections
		self.settings_dict = settings_dict

		self.account = settings_dict['ACCOUNT']
		self.host = settings_dict['ACCOUNT']+'.blob.'+settings_dict['ENDPOINT']

		self.block_blob_service = BlockBlobService(
			account_name=settings_dict['ACCOUNT'],
			account_key=settings_dict['KEY'],
			endpoint_suffix=settings_dict['ENDPOINT'])

	def create_container(self, container_name, set_public=False):
		"""
		Create a azure blob container.
		"""
		self.stdout.INFO("Creating the container [%s] on '%s'" % (container_name, self.host))

		if set_public:
			public_access = PublicAccess.Container
			self.stdout.INFO("Sets the container [%s] to public access." % container_name)
		else:
			public_access = None

		try:
			result = self.block_blob_service.create_container(
				container_name, fail_on_exist=True,
				timeout=self.settings_dict['TIMEOUT'],
				public_access=public_access)
		except AzureConflictHttpError as e:
			self.stdout.ERROR("The specified container [%s] does exist" % container_name)
			result = False

		return result

	def list_containers(self, prefix=None):
		self.stdout.INFO("Request to list containers on %s" % self.host)
		# An iterator to list all containers on blob
		icontainers = self.block_blob_service.list_containers(
			prefix=prefix, timeout=self.settings_dict['TIMEOUT'])

		# Converts an iterator to list
		container_names = [container for container in icontainers]

		self.stdout.INFO(
			"%d containers found on %s." % (len(container_names), self.host)
			)
		return container_names


	def list_blobs(self, container_name, prefix=None, suffix=None):
		"""
		Lists all blobs on the container, note that the blob_names returned
		are posix-style path, no matter what names were when create.
		"""
		blob_names = []
		self.stdout.INFO("Request to list blobs in container [%s]" % container_name)

		try:
			# An iterator to
			iblobs = self.block_blob_service.list_blobs(
				container_name, prefix=prefix, timeout=self.timeout)

			if suffix:
				blob_names = [blob for blob in iblobs if blob.endswith(suffix)]
			else:
				blob_names = [blob for blob in iblobs]

		except AzureMissingResourceHttpError as e:
			self.stdout.ERROR(
				"The specified container [%s] does not exist." % container_name
				)

		self.stdout.INFO(
			"%s blobs found on [%s]." % (len(blob_names), container_name)
			)
		return blob_names


	def create_blob_from_path(self, container_name, blob_name, filepath):
		"""
		Uploads a file to the container.

		Returns an instance of `Blob` with properties and metadata.
		"""
		if not os.path.exists(filepath):
			self.stdout.ERROR("'%s' does not exist." % filepath)
			return None

		blob = self.block_blob_service.create_blob_from_path(
			container_name, blob_name, filepath)
		return blob


	def upload(self, container_name, blob_pairs):
		"""
		Uploads files to the container on Azure. Note that 'blob_name' uploaded
		will be converted to posix-style names, which means sep for path is
		'/'.

		`blob_pairs`
			A tuple consists of 2 elements, blob_name and its filepath on local
			filesystem.
		"""
		if not self.block_blob_service.exists(container_name):
			self.create_container(container_name, set_public=True)

		blobs = []
		blobs_in_container = self.list_blobs(container_name)
		# TODO: show progress bar when uploading files
		for blob_name, filepath in blob_pairs:
			posix_blob_name = ppath(blob_name)
			if posix_blob_name not in blobs_in_container:
				blob = self.create_blob_from_path(
					container_name, posix_blob_name, filepath)
				if blob:
					blobs.append(blob)

		self.stdout.INFO("Uploads %d files to [%s]." % (len(blobs), container_name))
		return blobs


	def get_blob_to_path(self, container_name, blob_name, filepath):
		"""
		Gets a blob from the container. The filepath would be returned if gotten
		successfully.
		"""
		dirpath = os.path.dirname(filepath)
		if not os.path.exists(dirpath):
			os.makedirs(dirpath)

		blob = self.block_blob_service.get_blob_to_path(
			container_name, blob_name, filepath)
		return blob


	def download(self, container_name, dest, blob_names=None):
		"""
		Get blobs from the container to the `dest` directory.
		"""
		blobs = []

		if not self.block_blob_service.exists(container_name):
			self.stdout.ERROR("Container [%s] does not exist" % container_name)
		# Get the list of blobs and then do comparision would be much more efficient
		blobs_in_container = self.list_blobs(container_name)

		# Get all blobs if blob_names was not specified
		if not blob_names:
			blob_names = blobs_in_container

		for blob_name in blob_names:
			if ppath(blob_name) in blobs_in_container:
				dest_filepath = safe_join(dest, blob_name)
				# TODO: not sure posix-style path works for files on container
				# are windows-style
				blob = self.get_blob_to_path(container_name, ppath(blob_name), dest_filepath)
				blobs.append(blob)

		return blobs


	def get_blob_to_text(self, container_name, blob_name):
		pass


	def get_blobs(self, container_name, blob_names=None):
		pass


	def set_container_acl(self, container_name, set_public=True):
		if set_public:
			self.stdout.INFO("Set public read access to container [%s]." % container_name)
			public_access = PublicAccess.Container
		else:
			self.stdout.INFO("Set public read access to blobs on [%s]." % container_name)
			public_access = PublicAccess.Blob

		self.block_blob_service.set_container_acl(container_name, public_access=public_access)


	def delete_blobs(self, container_name, blob_names):
		blobs = []
		for blob_name in blob_names:
			try:
				blob = self.block_blob_service.delete_blob(container_name, blob_name)
				self.stdout.INFO(
					"Delete the blob %s from container [%s]" % (blob_name, container_name))
				blobs.append(blob)
			except AzureMissingResourceHttpError as e:
				self.stdout.WARNING(
					"The sepcified blob %s on [%s] does not exist" % (blob_name, container_name))

		return blobs


	def copy_blobs(self, container_name, blob_names, copy_source):
		pass

	def copy(self, src_container, dst_container):
		pass


azure = AzureBlobService(settings.AZURE, )
