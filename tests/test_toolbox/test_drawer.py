# -*- coding: utf-8 -*-
import unittest
import numpy as np

from moose.toolbox.image import drawer

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
            self.assertEqual(im[x, y].tolist(), value)

class PointTestCase(BaseShapeTestCase):
    valid_dataset   = [((10, 10), 'a'), ((25, 25), 'b')]
    invalid_dataset = [((-1, -1), 'b'), ((3000, 3000), 'c')]
    test_dataset    = [((10, 10), (255, 0, 0)),
                        ((11, 10), (255, 0, 0)),
                        ((25, 24), (255, 0, 0)),
                        ]
    shape_class     = drawer.Point
