# -*- coding: utf-8 -*-
import mock
import unittest

from moose.toolbox.image import colors
from moose.core.exceptions import ImproperlyConfigured

class ColorsTestCase(unittest.TestCase):

    def test_choice(self):
        a = colors.choice()
        self.assertIn(a, colors._colors)

        b = colors.choice(exclude=[a])
        self.assertIn(b, colors._colors)
        self.assertNotEqual(a, b)

        with self.assertRaises(ImproperlyConfigured):
            colors.choice(exclude=colors._colors)
