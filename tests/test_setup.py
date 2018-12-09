# -*- coding: utf-8 -*-
import mock
import unittest
import moose

class SetupTestCase(unittest.TestCase):

    def test_get_version(self):
        self.assertRegexpMatches(moose.__version__, '[\d\.ab]+')

        # won't raise UnicodeDecodeError
        with self.assertRaises(IOError):
            moose.__file__ = u"/测试/路径/__init__.py".encode('gbk')
            moose.get_version()

        moose.__file__ = u"tests/sample_data/setup/版本/__init__.py".encode('utf-8')
        self.assertRegexpMatches(moose.get_version(), '[\d\.ab]+')

    def test_setup(self):
        moose.setup()
        # TODO: tests if logger and settings was configured
