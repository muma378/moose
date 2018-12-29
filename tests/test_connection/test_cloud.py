# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import os
from os.path import abspath, join
import unittest
import mock
import platform
from azure.storage.blob import BlockBlobService, PublicAccess
from azure.common import AzureConflictHttpError, AzureMissingResourceHttpError
from moose.utils import six
from moose.connection.cloud import AzureBlobService
from moose.core.exceptions import \
    ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured

from .config import azure_settings


if platform.system()=="Windows":
    expandpath = lambda x: abspath(x.replace('/', '\\'))
else:
    expandpath = lambda x: abspath(x)

class AzureBlobServiceTest(unittest.TestCase):

    def setUp(self):
        self.azure_patcher = mock.patch("moose.connection.cloud.BlockBlobService")
        self.mock_azure = self.azure_patcher.start()
        self.mock_blob_service = mock.MagicMock(spec=BlockBlobService)
        self.mock_azure.return_value = self.mock_blob_service
        # creates a mock instance of `AzureBlobService`
        self.azure_handler = AzureBlobService(azure_settings)

    def tearDown(self):
        self.mock_azure = self.azure_patcher.stop()

    def test_azure_init(self):
        azure_handler = AzureBlobService(azure_settings)
        # tests if it was initialized with params in `config`
        self.mock_azure.assert_called_with(
            account_name='test',
            account_key='<password>',
            endpoint_suffix='endpoint'
        )
        self.assertEqual(azure_handler.host, 'test.blob.endpoint')
        self.assertEqual(azure_handler.block_blob_service, self.mock_blob_service)

    def test_create_container(self):
        # tests if container was created with proper params
        self.azure_handler.create_container('test')
        self.mock_blob_service.create_container.assert_called_with(
            'test', fail_on_exist=True, timeout=300, public_access=None
        )

        self.azure_handler.create_container('test', set_public=True)
        self.mock_blob_service.create_container.assert_called_with(
            'test', fail_on_exist=True, timeout=300,
            public_access=PublicAccess.Container
        )

        self.mock_azure.reset_mock()
        # tests if it was muted when an error occured at creating containers
        self.mock_blob_service.create_container = mock.Mock(side_effect=AzureConflictHttpError('a', 'b'))
        self.assertEqual(
            self.azure_handler.create_container('test'), False)
        self.assertEqual(
            self.azure_handler.create_container('test', set_public=True),
            False)

    def test_list_containers(self):
        self.azure_handler.list_containers()
        self.mock_blob_service.list_containers.assert_called_with(
            prefix=None, timeout=300
        )

        self.azure_handler.list_containers(prefix="test-")
        self.mock_blob_service.list_containers.assert_called_with(
            prefix="test-", timeout=300
        )
        self.assertTrue(isinstance(self.azure_handler.list_containers(), list))

    def test_list_blobs(self):
        # Since “name” is an argument to the Mock constructor,
        # if you want your mock object to have a “name” attribute
        # you can’t just pass it in at creation time.
        mock_obj1 = mock.MagicMock()
        mock_obj1.name = "a.txt"
        mock_obj2 = mock.MagicMock()
        mock_obj2.name = "a.wav"
        mock_obj3 = mock.MagicMock()
        mock_obj3.name = "a.metadata"

        self.mock_blob_service.list_blobs.return_value = [mock_obj1, mock_obj2, mock_obj3]
        six.assertCountEqual(
            self,
            self.azure_handler.list_blobs('test'),
            ["a.txt", "a.wav", "a.metadata"])
        self.mock_blob_service.list_blobs.assert_called_with(
            'test', prefix=None, timeout=300)

        six.assertCountEqual(
            self,
            self.azure_handler.list_blobs('test', prefix="test-", suffix=".wav"),
            ["a.wav"])
        self.mock_blob_service.list_blobs.assert_called_with(
            'test', prefix="test-", timeout=300)

        six.assertCountEqual(
            self,
            self.azure_handler.list_blobs('test', suffix=(".wav", ".txt")),
            ["a.wav", "a.txt"])
        self.mock_blob_service.list_blobs.assert_called_with(
            'test', prefix=None, timeout=300)

        self.mock_azure.reset_mock()
        self.mock_blob_service.list_blobs = mock.Mock(
            side_effect=AzureMissingResourceHttpError('a', 'b'))
        six.assertCountEqual(
            self,
            self.azure_handler.list_blobs('test', suffix=(".wav", ".txt")),
            [])

    @mock.patch('moose.connection.cloud.os')
    def test_create_blob_from_path(self, mock_os):
        mock_os.path.exists.return_value = False
        self.assertEqual(
            self.azure_handler.create_blob_from_path("test", 'blobname', 'filepath'),
            None
        )

        mock_os.path.exists.return_value = True
        self.azure_handler.create_blob_from_path("test", 'blobname', 'filepath')
        self.mock_blob_service.create_blob_from_path.assert_called_with(
            "test", 'blobname', 'filepath')

    @mock.patch.object(AzureBlobService, 'list_blobs')
    @mock.patch.object(AzureBlobService, 'create_container')
    @mock.patch.object(AzureBlobService, 'create_blob_from_path')
    def test_upload(self, mock_create_blob, mock_create_container, mock_list_blobs):
        blob_pairs = [
            ('to/blob1.txt', '/path/to/file1.txt'),
            ('to\\blob2.txt', '\\path\\to\\file2.txt'),
            ('to\\blob3.txt', '/path/to/file3.txt'),
        ]

        # container and some blobs were created before,
        # and upload with overwritting
        self.mock_blob_service.exists = mock.Mock(return_value=True)
        mock_list_blobs.return_value = ['to/blob1.txt', 'to/blob2.txt']
        six.assertCountEqual(
            self,
            self.azure_handler.upload('test', blob_pairs, overwrite=False),
            ['to/blob3.txt', ]
        )
        mock_create_container.assert_not_called()
        mock_create_blob.assert_called_with('test', 'to/blob3.txt', '/path/to/file3.txt')

        # upload with `overwrite` set to True
        mock_create_blob.reset_mock()
        six.assertCountEqual(
            self,
            self.azure_handler.upload('test', blob_pairs, overwrite=True),
            ['to/blob1.txt', 'to/blob2.txt', 'to/blob3.txt']
        )
        self.azure_handler.upload('test', blob_pairs, overwrite=True)
        mock_create_container.assert_not_called()
        mock_create_blob.assert_has_calls(
            [
                mock.call('test', 'to/blob1.txt', '/path/to/file1.txt'),
                mock.call('test', 'to/blob2.txt', '\\path\\to\\file2.txt'),
                mock.call('test', 'to/blob3.txt', '/path/to/file3.txt')
            ]
        )

        # container was not exist
        self.mock_blob_service.exists = mock.Mock(return_value=False)
        self.azure_handler.upload('test', blob_pairs, overwrite=False)
        mock_create_container.assert_called_with(
            'test', set_public=True)

    @mock.patch('moose.connection.cloud.os')
    def test_get_blob_to_path(self, mock_os):
        mock_os.path.dirname = os.path.dirname
        mock_os.path.exists.return_value = False
        self.azure_handler.get_blob_to_path("test", "to/blob1.txt", "/path/to/blob1.txt"),
        mock_os.makedirs.assert_called_with("/path/to")
        self.mock_blob_service.get_blob_to_path.assert_called_with(
            "test", "to/blob1.txt", "/path/to/blob1.txt")

    @mock.patch.object(AzureBlobService, 'list_blobs')
    @mock.patch.object(AzureBlobService, 'get_blob_to_path')
    def test_download(self, mock_get_blob, mock_list_blobs):

        # case 1. the container does not exist
        self.mock_blob_service.exists = mock.Mock(return_value=False)
        self.assertEqual(
            self.azure_handler.download('test', 'dest'),
            [])
        self.assertEqual(
            self.azure_handler.download('test', 'dest', blob_names=["blob1.txt"]),
            [])

        # case 2. the container exists and `blob_names` was not specified
        self.mock_blob_service.exists = mock.Mock(return_value=True)
        mock_list_blobs.return_value = [
            'to/blob1.txt', 'to/blob2.txt', 'to/blob3.txt'
        ]
        six.assertCountEqual(
            self,
            self.azure_handler.download('test', 'dest'),
            ['to/blob1.txt', 'to/blob2.txt', 'to/blob3.txt'])

        mock_get_blob.assert_has_calls(
            [
                mock.call("test", "to/blob1.txt", expandpath("dest/to/blob1.txt")),
                mock.call("test", "to/blob2.txt", expandpath("dest/to/blob2.txt")),
                mock.call("test", "to/blob3.txt", expandpath("dest/to/blob3.txt")),
            ])

        # case 3. the container exists and `blob_names` was specified
        blob_names = ['to/blob1.txt', 'to\\blob2.txt', ]
        mock_get_blob.reset_mock()
        six.assertCountEqual(
            self,
            self.azure_handler.download('test', 'dest', blob_names=blob_names),
            ['to/blob1.txt', 'to\\blob2.txt'])

        mock_get_blob.assert_has_calls(
            [
                mock.call("test", "to/blob1.txt", expandpath("dest/to/blob1.txt")),
                mock.call("test", "to/blob2.txt", expandpath("dest/to/blob2.txt")),
            ])


        missing_blob_names = ['to/blob1.txt', 'to/blob4.txt', ]
        mock_get_blob.reset_mock()
        six.assertCountEqual(
            self,
            self.azure_handler.download('test', 'dest', blob_names=missing_blob_names),
            ['to/blob1.txt'])

        mock_get_blob.assert_called_with(
            "test", "to/blob1.txt", expandpath("dest/to/blob1.txt"))


    def test_set_container_acl(self):
        self.azure_handler.set_container_acl('test', set_public=True)
        self.mock_blob_service.set_container_acl.assert_called_with(
            'test', public_access=PublicAccess.Container)

        self.mock_azure.reset_mock()
        self.azure_handler.set_container_acl('test', set_public=False)
        self.mock_blob_service.set_container_acl.assert_called_with(
            'test', public_access=PublicAccess.Blob)

    def test_delete_blobs(self):
        blob_names = [
            'to/blob1.txt', 'to/blob2.txt', 'to/blob3.txt'
        ]
        self.azure_handler.delete_blobs('test', blob_names)
        self.mock_blob_service.delete_blob.assert_has_calls(
            [
                mock.call('test', 'to/blob1.txt'),
                mock.call('test', 'to/blob2.txt'),
                mock.call('test', 'to/blob3.txt'),
            ])

        self.mock_azure.reset_mock()
        self.mock_blob_service.delete_blob = mock.Mock(side_effect=AzureMissingResourceHttpError('A', 'B'))  # 判断抛错
        six.assertCountEqual(
            self,
            self.azure_handler.delete_blobs('test', blob_names),
            [])

    @mock.patch.object(AzureBlobService, 'list_blobs')
    def test_copy_blobs(self, mock_list_blobs):
        # case 1. `blob_names` was set to None but src_container was given
        mock_list_blobs.return_value = [
            'to/blob1.txt', 'to/blob1.wav', 'to/blob2.txt'
        ]
        azure_host = "test.blob.endpoint"
        six.assertCountEqual(
            self,
            self.azure_handler.copy_blobs(None, 'test', src_container='source'),  # 可以匹配所有的
            ['to/blob1.txt', 'to/blob1.wav', 'to/blob2.txt'])

        self.mock_blob_service.copy_blob.assert_has_calls(
            [
                mock.call('test', 'to/blob1.txt', 'http://{}/source/to/blob1.txt'.format(azure_host)),
                mock.call('test', 'to/blob1.wav', 'http://{}/source/to/blob1.wav'.format(azure_host)),
                mock.call('test', 'to/blob2.txt', 'http://{}/source/to/blob2.txt'.format(azure_host)),
            ])

        six.assertCountEqual(
            self,
            self.azure_handler.copy_blobs(None, 'test', src_container='source', pattern='*.wav'),
            ['to/blob1.wav'])
        six.assertCountEqual(
            self,
            self.azure_handler.copy_blobs(None, 'test', src_container='source', pattern='*.txt'),
            ['to/blob1.txt', 'to/blob2.txt'])

        # if src_container is None
        self.mock_azure.reset_mock()
        with self.assertRaises(ImproperlyConfigured):
            self.azure_handler.copy_blobs(None, 'test', None)

    @mock.patch.object(AzureBlobService, 'list_blobs')
    def test_copy_container(self, mock_list_blobs):
        mock_list_blobs.return_value = [
            'to/blob1.txt', 'to/blob1.wav', 'to/blob2.txt'
        ]
        azure_host = "test.blob.endpoint"

        self.azure_handler.copy_container('source', 'test', pattern=None)
        self.mock_blob_service.create_container.assert_called_with(
            'test', fail_on_exist=True, timeout=300,
            public_access=PublicAccess.Container
        )

        self.mock_blob_service.copy_blob.assert_has_calls([
            mock.call('test', 'to/blob1.txt', 'http://{}/source/to/blob1.txt'.format(azure_host)),
            mock.call('test', 'to/blob1.wav', 'http://{}/source/to/blob1.wav'.format(azure_host)),
            mock.call('test', 'to/blob2.txt', 'http://{}/source/to/blob2.txt'.format(azure_host))
        ])
