# -*- coding: utf-8 -*-
import unittest
import logging
from cStringIO import StringIO
from smb.smb_structs import OperationFailure
from smb.base import NotConnectedError

from moose.connection.cifs import SMBConnProxy

SMB = {
    'HOST': '10.10.8.123',
    'PORT': 139, # 139 if using NetBIOS over tcp/ip, 445 if direct hosting over tcp/ip
    'USERNAME': '<username>',
    'PASSWORD': '<password>',
    'DOMAIN': 'DATATANG',   # workgroup, it is safe to leave it empty
    'CLIENT_NAME': 'DATATANG',  # an arbitary ASCII string
    'SERVER_NAME': 'test-5-11',
    # NTLMv1 or NTLMv2 authentication will be used, guess to be True for WIN7, Vista
    'NTLMv2': True,
}


smb_conn = SMBConnProxy(SMB)

class SMBConnProxyTestCase(unittest.TestCase):
    def setUp(self):
        self.smb_proxy = smb_conn
        self.test_list = (
            u'/smbtest/test0/1',
            u'/smbtest/test0/2',
            u'/smbtest/test0/3',
            u'/smbtest/test0/4',
            u'/smbtest/test0/test0_0/5',
            u'/smbtest/test0/test0_1/6',
        )

    def test_connect(self):
        self.assertEqual(self.smb_proxy.smb_conn.echo('hello'), 'hello', 'connected failed')
        self.assertNotEqual(self.smb_proxy.smb_conn.echo('hello1'), 'hello', 'connected failed')
        self.smb_proxy.smb_conn.close()

        with self.assertRaises(NotConnectedError):
            self.assertEqual(self.smb_proxy.smb_conn.echo('hello'), 'hello', 'connected failed')

        self.smb_proxy.connect()
        self.assertEqual(self.smb_proxy.smb_conn.echo('hello'), 'hello', 'connected failed')
        self.assertNotEqual(self.smb_proxy.smb_conn.echo('hello1'), 'hello', 'connected failed')

    def test_is_connected(self):
        if not self.smb_proxy.smb_conn.echo('hello') == 'hello':
            self.smb_proxy.connect()
            self.assertTrue(self.smb_proxy.is_connected)
        self.smb_proxy.smb_conn.close()
        self.assertFalse(self.smb_proxy.is_connected)

    def test_override(self):
        try:
            self.assertEqual(self.smb_proxy.echo('hello'), 'hello')
        except AttributeError, e:
            self.fail('__override test failed')

    def test_retrieve_file(self):
        if not self.smb_proxy.is_connected:
            self.smb_proxy.connect()
        file_obj = StringIO()
        self.smb_proxy.retrieve_file(u'14.肖旸', u'/smbtest/test0/1', file_obj)
        self.assertEqual(file_obj.getvalue(), '1', 'failed to retrieve files')
        file_obj.close()

        file_obj = StringIO()
        self.smb_proxy.retrieve_file(u'14.肖旸', u'/smbtest/test0/3', file_obj)
        self.assertEqual(file_obj.getvalue(), '3', 'failed to retrieve files')
        file_obj.close()

        self.smb_proxy.close()
        file_obj = StringIO()
        try:
            self.smb_proxy.retrieve_file(u'14.肖旸', u'/smbtest/test0/2', file_obj)
            self.assertEqual(file_obj.getvalue(), '2', 'failed to auto reconnect')
        except NotConnectedError, e:
            self.fail('failed to auto reconnect when retrieving files')
        finally:
            file_obj.close()

    def test_get_filelist(self):
        def filelist_test():
            test_list = list(self.test_list)

            filelist = self.smb_proxy.get_filelist(u'14.肖旸', u'/smbtest/test0')
            for device, path in filelist:
                try:
                    i = test_list.index(path)
                    self.assertTrue(i!=-1, 'redundant path matched: %s' % path)
                    test_list.pop(i)
                except ValueError, e:
                    self.fail('redundant path matched: %s' % path)
                # empty list
            self.assertFalse(test_list, 'unable to find all files')

        if not self.smb_proxy.is_connected:
            self.smb_proxy.connect()
        filelist_test()
        # test if the connection could be established automatically
        self.smb_proxy.close()
        filelist_test()

    def test_retrieve(self):
        files_found = self.smb_proxy.retrieve(
            dirs=[u'/14.肖旸/smbtest/test0/test0_0', u'/14.肖旸/smbtest/test0/test0_1'])
        files_inside = (
            (u'smbtest/test0/test0_0/5', ),
            (u'smbtest/test0/test0_1/6', )
        )
        device_inside = (u'14.肖旸', u'14.肖旸')

        for i, files in enumerate(files_found):
            for name, path in files:
                self.assertEqual(name, device_inside[i], 'device found not matched')
                self.assertTrue((path in files_inside[i]), 'redundant path matched: %s' % path)

        files_found = self.smb_proxy.retrieve(dirs=(u'/14.肖旸/smbtest/test1', ), pattern='*.txt')
        for files in files_found:
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0][1], u'smbtest/test1/diff.txt', 'the argument pattern is useless')

        files_found = self.smb_proxy.retrieve(dirs=('1234', '5678'))
        with self.assertRaises(StopIteration):
            next(files_found)
