# -*- coding: utf-8 -*-
import unittest

import codecs
from moose.utils import encoding

class BomRemovalTestCase(unittest.TestCase):

    def setUp(self):
        self.s = u"单元测试用例1"

    def test_unicode(self):
        self.assertEqual(encoding.remove_bom(self.s), self.s)

    def test_utf8_bom(self):
        s = self.s.encode("utf-8-sig")
        self.assertEqual(encoding.remove_bom(s), self.s.encode("utf-8"))

    def test_utf16_bom(self):
        s = self.s.encode("utf-16")
        self.assertEqual(encoding.remove_bom(s), s[2:])

    def test_utf32_bom(self):
        s = self.s.encode("utf-32")
        self.assertEqual(encoding.remove_bom(s), s[4:])
