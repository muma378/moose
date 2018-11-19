# -*- coding: utf-8 -*-
import unittest
import mock

from azure.storage.blob import BlockBlobService, PublicAccess
from azure.common import AzureConflictHttpError, AzureMissingResourceHttpError
from moose.connection.cloud import AzureBlobService
from moose.core.exceptions import \
ConnectionTimeout, SuspiciousOperation, ImproperlyConfigured

from .config import azure_settings

class AzureBlobServiceTest(unittest.TestCase):

    def setUp(self):
        '''
        在这里将对象实例化
        '''
        self.azure_patcher = mock.patch("moose.connection.cloud.BlockBlobService")  # 这里是对整个类进行模拟
        self.mock_azure = self.azure_patcher.start()
        self.mock_blob_service = mock.MagicMock(spec=BlockBlobService)
        # 模拟一个blob_service对象,MagicMock中传入spec的类默认包含双下方法
        self.mock_azure.return_value = self.mock_blob_service  # mock_block_blob_service 是模拟一个mock对象，要模拟什么方法只需要.方法即可
        self.azure_handler = AzureBlobService(azure_settings)  # 实例化被测试对象

    def test_azure_init(self):
        azure_handler = AzureBlobService(azure_settings)  # 实例化被测试对象
        self.mock_azure.assert_called_with(
            account_name='<test>',
            account_key='<password>',
            endpoint_suffix='<endpoint>'
            )
        self.assertEqual(azure_handler.host, '<test>.blob.<endpoint>')
        self.assertEqual(azure_handler.block_blob_service, self.mock_blob_service)


    def test_create_container(self):
        self.azure_handler.create_container('test')
        self.mock_blob_service.create_container.assert_called_with(
            'test', fail_on_exist=True, timeout=300, public_access=None
            )

        self.azure_handler.create_container('test', set_public=True)
        self.mock_blob_service.create_container.assert_called_with(
            'test', fail_on_exist=True, timeout=300, public_access=PublicAccess.Container
            )

        self.mock_azure.reset_mock()  # 重置mock对象
        self.mock_blob_service.create_container = mock.Mock(side_effect=AzureConflictHttpError('a', 'b'))  # 判断抛错
        self.assertEqual(self.azure_handler.create_container('test'), False)
        self.assertEqual(self.azure_handler.create_container('test', set_public=True), False)

    def test_list_containers(self):
        self.azure_handler.list_containers()  # 调用该方法
        self.mock_block_blob_service.list_containers.assert_called_with(timeout=300)  # 是不是通过某个参数调用的

        self.assertEqual(self.azure_handler.list_containers(),
                         self.mock_block_blob_service.list_containers())  # 判断返回值是否相等

        with self.assertRaises(TypeError):
            self.azure_handler.list_containers(True)

        # with self.assertRaises(ImproperlyConfigured):  # 捕获异常
        #     self.azure_handler.

    @mock.patch.object(AzureBlobService, 'container_name')  # 保证container不变
    def test_list_blobs(self, mock_container_name):
        self.azure_handler.list_blobs('test')
        self.mock_block_blob_service.list_blobs.assert_called_with('test')  # 是不是通过某个参数调用的
        self.mock_block_blob_service.list_blobs.assert_called_with(suffix=None)

        self.mock_azure.reset_mock()  # 重置mock对象
        self.azure_handler.list_blobs('test', suffix=True)
        self.mock_block_blob_service.list_blobs.assert_called_with(suffix=True)

        self.assertEqual(self.azure_handler.list_blobs('test'),
                         self.mock_block_blob_service.list_blobs('test'))  # 判断返回值是否相等

        self.mock_azure.reset_mock()  # 重置mock对象
        self.mock_block_blob_service.list_blobs = mock.Mock(side_effect=AzureMissingResourceHttpError)  # 判断抛错是否相等

    @mock.patch('moose.connection.cloud.os')
    def test_create_blob_from_path(self, mock_os):
        # 路径存在不存在如何进行断言

        mock_os.path.exist.return_value = False  # 设置默认值

        self.azure_handler.create_blob_from_path("any path", 'blobname', 'filepath')

        self.mock_block_blob_service.create_blob_from_path.assert_not_called("any path")

        mock_os.path.exist.return_value = True

        self.azure_handler.create_blob_from_path("any path", 'blobname', 'filepath')

        self.mock_block_blob_service.create_blob_from_path.assert_called_with("any path")

        self.assertEqual(self.azure_handler.create_blob_from_path("any path", 'blobname', 'filepath'),
                         self.mock_block_blob_service.create_blob_from_path('test'))  # 判断返回值是否相等

        # mock_container_name.assert_called_with('test')
        self.mock_azure.reset_mock()
        self.azure_handler.create_blob_from_path('test', 'a', 'b', 'c')  # 多传一个参数
        self.mock_block_blob_service.create_blob_from_path = mock.Mock(side_effect=ValueError)  # 判断抛错

    @mock.patch('moose.connection.cloud.BlockBlobService')
    def test_upload(self, mock_BlockBlobService):
        # 关键点1  如果容器不存在
        container_name = 'haha'
        blob_pairs = []
        mock_BlockBlobService.exists.return_value = False
        self.azure_handler.upload(container_name, blob_pairs, overwrite=True)
        self.mock_azure.create_container.assert_called_with('containername', 'blob_pairs', overwrite=False)
        self.mock_block_blob_service.create_container.upload(overwrite=True)

        self.mock_azure.create_blob_from_path.assert_called_with()  # 被调用

        # 关键点2  如果overwrite为True 或者为false
        # 调用函数，看看参数有没有被调用

        self.mock_azure.reset_mock()

        self.azure_handler.upload('test', blob_pairs, overwrite=False)

        self.mock_block_blob_service.create_container.upload(overwrite=False)

    @mock.patch('moose.connection.cloud.os')
    def test_get_blob_to_path(self, mock_os):
        mock_os.path.exist.return_value = True  # 设置默认值

        self.azure_handler.get_blob_to_path("any path")

        self.mock_azure.get_blob_to_path.assert_not_called("any path")

        # set up the mock
        mock_os.path.exist.return_value = False

        self.azure_handler.block_blob_service.get_blob_to_path("any path")

        self.mock_azure.get_blob_to_path.assert_not_called("any path")

        mock_os.makedirs.assert_called_with('any path')  # makedirs是否被调用

        # 关键点2 调用的参数是否符合要求

        self.mock_azure.reset_mock()
        self.azure_handler.block_blob_service.get_blob_to_path('test', 'a', 'b', 'c')  # 多传一个参数
        self.mock_block_blob_service.get_blob_to_path = mock.Mock(side_effect=ValueError)  # 判断抛错

    @mock.patch('moose.connection.cloud.BlockBlobService')
    def test_download(self, mock_BlockBlobService):
        mock_BlockBlobService.exists.return_value = False
        self.assertEqual(self.azure_handler.download('test', 'dest', blob_names=None), [])

        # 断言参数是否被调用
        self.azure_handler.download('test', 'dest', blob_names=None)
        self.mock_block_blob_service.download.assert_called_with(blob_names=None)  # 是不是通过某个参数调用的

    def test_set_container_acl(self):
        container_name = 'test'
        # 判断set_public
        self.azure_handler.set_container_acl(container_name, set_public=True)
        self.mock_block_blob_service.create_container.assert_called_with('test')  # 是不是通过某个参数调用的
        self.mock_block_blob_service.set_container_acl.assert_called_with(set_public=True)
        self.mock_azure.reset_mock()
        self.azure_handler.set_container_acl(container_name)
        self.mock_block_blob_service.create_container.assert_called_with('test')  # 是不是通过某个参数调用的
        self.mock_block_blob_service.set_container_acl.assert_called_with(set_public=False)

    def test_delete_blobs(self):
        container_name = 'test'
        self.mock_block_blob_service.block_blob_service.list_blobs.assert_called_with(container_name, "blob_name")

        self.mock_azure.reset_mock()  # 重置mock对象
        self.mock_block_blob_service.delete_blobs = mock.Mock(side_effect=AzureMissingResourceHttpError)  # 判断抛错
        self.mock_block_blob_service.block_blob_service.list_blobs.assert_not_called(container_name, "blob_name")

    def test_copy_blobs(self):
        blob_names = None
        container_name = 'test'
        src_container = ''
        self.azure_handler.copy_blobs(None, container_name, src_container=src_container)
        self.mock_block_blob_service.copy_blobs.assert_called_with(blob_names)
        self.mock_block_blob_service.list_blobs.assert_called_with(src_container)

        with self.assertRaises(ImproperlyConfigured):
            self.azure_handler.list_blobs(src_container)

    def test_copy_container(self):
        pass

    def tearDown(self):
        self.mock_azure = self.azure_patcher.stop()
