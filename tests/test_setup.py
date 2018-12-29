# -*- coding: utf-8 -*-
import mock
import unittest
import moose
from moose.utils import six

import platform
if platform.system()=="Windows":
    npath = lambda x: x.replace('/', '\\').encode("gbk")
else:
    npath = lambda x: x.encode("utf-8")

class SetupTestCase(unittest.TestCase):

    def test_get_version(self):
        self.assertRegexpMatches(moose.__version__, '[\d\.ab]+')

        if six.PY2:
            # if moose was installed under a path with chinese characters
            moose.__file__ = npath(u"tests/sample_data/setup/版本/__init__.py")
            self.assertRegexpMatches(moose.get_version(), '[\d\.ab]+')

    def test_setup(self):
        moose.setup()
        # TODO: tests if logger and settings was configured
