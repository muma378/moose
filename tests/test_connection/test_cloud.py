# -*- coding:utf-8 -*-


import sys  # 要重新载入sys。因为 Python 初始化后会删除 sys.setdefaultencoding 这个方 法

reload(sys)
sys.setdefaultencoding('utf-8')
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
        self.mock_blob_service.list_containers.assert_called_with(prefix=None, timeout=300)  # 是不是通过某个参数调用的

        self.assertTrue(isinstance(self.azure_handler.list_containers(), list))

    def test_list_blobs(self):
        self.azure_handler.list_blobs('test')
        self.mock_blob_service.list_blobs.assert_called_with('test', prefix=None, timeout=300)  # 是不是通过某个参数调用的

        self.mock_azure.reset_mock()  # 重置mock对象
        self.azure_handler.list_blobs('test', suffix=True)
        self.mock_blob_service.list_blobs.assert_called_with('test', prefix=None, timeout=300)

        self.mock_azure.reset_mock()  # 重置mock对象
        self.mock_blob_service.list_blobs = mock.Mock(side_effect=AzureMissingResourceHttpError('a', 'b'))  # 判断抛错是否相等

    @mock.patch('moose.connection.cloud.os')
    def test_create_blob_from_path(self, mock_os):
        # 路径存在不存在如何进行断言

        mock_os.path.exists.return_value = False  # 设置默认值

        self.azure_handler.create_blob_from_path("test", 'blobname', 'filepath')

        # self.mock_blob_service.create_blob_from_path.assert_not_called()
        self.assertEqual(self.azure_handler.create_blob_from_path("test", 'blobname', 'filepath'), None)

        mock_os.path.exists.return_value = True

        self.azure_handler.create_blob_from_path("test", 'blobname', 'filepath')

        self.mock_blob_service.create_blob_from_path.assert_called_with("test", 'blobname', 'filepath')

        # mock_container_name.assert_called_with('test')
        self.mock_azure.reset_mock()
        self.azure_handler.create_blob_from_path('test', 'a', 'b')  # 多传一个参数
        self.mock_blob_service.create_blob_from_path = mock.Mock(side_effect=ValueError)  # 判断抛错

    #

    def test_upload(self):
        blob_pairs = []
        # 关键点1  如果容器不存在
        self.mock_blob_service.exists = mock.Mock(return_value=True)
        # mock_exists.return_value = False
        self.azure_handler.upload('test', blob_pairs, overwrite=False)
        self.mock_blob_service.create_container.assert_not_called()
        self.mock_blob_service.create_blob_from_path.assert_not_called()

        #
        self.mock_azure.reset_mock()

        self.mock_blob_service.exists = mock.Mock(return_value=False)
        self.azure_handler.upload('test', blob_pairs, overwrite=False)
        self.mock_blob_service.create_container.assert_called_with('test', fail_on_exist=True,
                                                                   timeout=300,
                                                                   public_access=PublicAccess.Container)

    #
    @mock.patch('moose.connection.cloud.os')
    def test_get_blob_to_path(self, mock_os):
        dirname = mock_os.path.dirname('filepath')

        mock_os.path.exists.return_value = False

        self.azure_handler.get_blob_to_path("test", 'blob_name', 'filepath')

        mock_os.makedirs.assert_called_with(dirname)  # makedirs是否被调用

        self.mock_azure.reset_mock()

        mock_os.path.exist.return_value = True  # 设置默认值

        self.azure_handler.get_blob_to_path("test", 'blob_name', 'filepath')

        self.mock_azure.get_blob_to_path.assert_not_called()

        # set up the mock
        self.mock_blob_service.get_blob_to_path.assert_called_with("test", 'blob_name', 'filepath')

        # 关键点2 调用的参数是否符合要求

        self.mock_azure.reset_mock()
        self.azure_handler.block_blob_service.get_blob_to_path('test', 'a', 'b', 'c')  # 多传一个参数
        self.mock_blob_service.get_blob_to_path = mock.Mock(side_effect=ValueError)  # 判断抛错

    #

    def test_download(self):
        self.mock_blob_service.exists = mock.Mock(return_value=True)
        self.azure_handler.download('test', 'dest')
        self.assertEqual(self.azure_handler.download('test', 'dest', blob_names=None), [])

        #     # 断言参数是否被调用
        self.mock_azure.reset_mock()
        blobs_in_container = self.azure_handler.list_blobs('test')

        # 没写完

    #     self.azure_handler.download('test', 'dest', blob_names=None)
    #     self.mock_blob_service.download.assert_called_with(blob_names=None)  # 是不是通过某个参数调用的
    # #
    def test_set_container_acl(self):
        # 判断set_public
        self.azure_handler.set_container_acl('test', set_public=True)
        self.mock_blob_service.set_container_acl.assert_called_with('test',
                                                                    public_access=PublicAccess.Container)  # 是不是通过某个参数调用的

        self.mock_azure.reset_mock()

        self.azure_handler.set_container_acl('test', set_public=False)
        self.mock_blob_service.set_container_acl.assert_called_with('test',
                                                                    public_access=PublicAccess.Blob)  # 是不是通过某个参数调用的

    def test_delete_blobs(self):
        self.azure_handler.delete_blobs('test', [])
        # self.mock_blob_service.delete_blob.assert_called_with('test', '')     #循环情况   ？？？？、

        self.mock_azure.reset_mock()  # 重置mock对象
        self.mock_blob_service.delete_blob = mock.Mock(side_effect=AzureMissingResourceHttpError('A', 'B'))  # 判断抛错
        self.mock_blob_service.delete_blob.assert_not_called()
        self.assertEqual(self.azure_handler.delete_blobs('test', []), [])  # 抛错，没有向列表添加

    def test_copy_blobs(self):
        blob_names = None
        container_name = 'test'
        src_container = 'abc'
        self.azure_handler.copy_blobs(blob_names, container_name, src_container=src_container)
        self.mock_blob_service.list_blobs.assert_called_with(src_container, prefix=None, timeout=300)

        self.mock_azure.reset_mock()

        with self.assertRaises(ImproperlyConfigured):  # blob_names, src_container都是None 应该抛错
            self.azure_handler.copy_blobs(None, 'test', None)

    def tearDown(self):
        
        self.mock_azure = self.azure_patcher.stop()
