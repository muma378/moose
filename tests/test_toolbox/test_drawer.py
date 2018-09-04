# -*- coding: utf-8 -*-
import unittest
import numpy as np

from moose.toolbox.image import drawer
from moose.conf import settings

BACKGROUND      = (0, 0, 0)

class BaseShapeTestCase(unittest.TestCase):

    valid_dataset   = []
    invalid_dataset = []
    test_dataset    = []
    shape_class     = None
    image_shape     = (2048, 2048, 3)

    def test_init(self):
        if self.shape_class == None:
            # do not test BaseShape
            return
        for coordinates, label in self.valid_dataset:
            try:
                shape = self.shape_class(coordinates, label)
                self.assertTrue(True)
            except drawer.InvalidCoordinates as e:
                self.assertTrue(False, "Raise error with valid coordinates: {}".format(coordinates))

        for coordinates, label in self.invalid_dataset:
            with self.assertRaises(drawer.InvalidCoordinates):
                shape = self.shape_class(coordinates, label)

    def test_draw_on(self):
        if self.shape_class == None:
            # do not test BaseShape
            return
        im = np.zeros(self.image_shape, np.uint8)
        for coordinates, label in self.valid_dataset:
            shape = self.shape_class(coordinates, label)
            shape.draw_on(im)

        for point, value in self.test_dataset:
            x, y = point
            self.assertEqual(im[y, x].tolist(), list(value), "Point(%s, %s) was not drawn." % (x, y))

class PointTestCase(BaseShapeTestCase):
    valid_dataset     = [
                        ((10, 10), 'a'),
                        ([25, 25], 'b'),
                        ((25.0, 28.23), 'b')
                        ]
    invalid_dataset   = [
                        (1, 'b'),
                        ((-1, -1), 'b'),
                        (('abc', 'def'), 'c')
                        ]
    test_dataset      = [
                        ((10, 10), settings.DEFAULT_COLOR),
                        ((11, 10), settings.DEFAULT_COLOR),
                        ((25, 24), settings.DEFAULT_COLOR),
                        ]
    shape_class     = drawer.Point

class LineStringTestCase(BaseShapeTestCase):
    valid_dataset     = [
                        ([[0, 0], [0, 10]], 'a'),
                        ([[1, 1], [10, 10]], 'a')
                        ]
    invalid_dataset   = [
                        (1, 'a'),
                        ([[0, 0]], 'a'),
                        ([[-1, 0], [0, 10]], 'a'),
                        ([[0, 0], [0, 10], [10, 10]], 'a'),
                        ]
    test_dataset      = [
                        ((0, 9), settings.DEFAULT_COLOR),
                        ((1, 9), settings.DEFAULT_COLOR),
                        ((9, 9), settings.DEFAULT_COLOR),
                        ((100, 1), BACKGROUND),
                        ]
    shape_class       = drawer.LineString
