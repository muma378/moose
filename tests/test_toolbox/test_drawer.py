# -*- coding: utf-8 -*-
import json
import unittest
import mock
import numpy as np

from moose.toolbox.image import drawer
from moose.conf import settings
from moose.core.exceptions import ImproperlyConfigured

BACKGROUND      = (0, 0, 0)

rev = lambda x: x[::-1]

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
            # notice it is im[y, x] not (x, y)
            self.assertEqual(im[y, x].tolist(), rev(list(value)), "Point(%s, %s) was not drawn." % (x, y))

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
                        ((100, 100), BACKGROUND),
                        ]
    shape_class     = drawer.Point

class LineStringTestCase(BaseShapeTestCase):
    valid_dataset     = [
                        ([[0, 0], [0, 10]], 'a'),
                        ([[1, 1], [10, 10]], 'a'),
                        ([[0, 0], [0, 10], [10, 10]], 'a'),
                        ]
    invalid_dataset   = [
                        (1, 'a'),
                        ([[0, 0]], 'a'),
                        ([[-1, 0], [0, 10]], 'a'),
                        ]
    test_dataset      = [
                        ((0, 9), settings.DEFAULT_COLOR),
                        ((1, 9), settings.DEFAULT_COLOR),
                        ((9, 9), settings.DEFAULT_COLOR),
                        ((100, 1), BACKGROUND),
                        ]
    shape_class       = drawer.LineString

class PolygonTestCase(BaseShapeTestCase):
    valid_dataset     = [
                        ([[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]], 'a'),
                        # add support for ring shape
                        ([[20, 20], [30, 30], [20, 20]], 'a')
                        ]
    invalid_dataset   = [
                        (1, 'a'),
                        ([[0, 0]], 'a'),
                        ([[-1, 0], [0, 10]], 'a'),
                        ([[0, 0], [0, 10], [10, 10]], 'a'),
                        ]
    test_dataset      = [
                        ((5, 5), settings.DEFAULT_COLOR),
                        ((10, 10), settings.DEFAULT_COLOR),
                        ((9, 9), settings.DEFAULT_COLOR),
                        ((100, 1), BACKGROUND),
                        ]
    outline_dataset   = [
                        ((0, 10), settings.DEFAULT_COLOR),
                        ((10, 10), settings.DEFAULT_COLOR),
                        ((25, 25), settings.DEFAULT_COLOR),
                        ((7, 7), BACKGROUND),
                        ((100, 1), BACKGROUND),
                        ]
    shape_class       = drawer.Polygon

    def test_outline(self):
        im = np.zeros(self.image_shape, np.uint8)
        for coordinates, label in self.valid_dataset:
            shape = self.shape_class(coordinates, label, filled=False)
            shape.draw_on(im)

        for point, value in self.outline_dataset:
            x, y = point
            # notice it is im[y, x] not (x, y)
            self.assertEqual(im[y, x].tolist(), rev(list(value)), "Point(%s, %s) was not drawn." % (x, y))

class RectangleTestCase(BaseShapeTestCase):
    valid_dataset     = [
                        ([[0, 0],[10, 10]], 'a'),
                        ([[8, 8], [20, 15]], 'a')
                        ]
    invalid_dataset   = [
                        (1, 'a'),
                        ([[0, 0]], 'a'),
                        ([[-1, 0], [0, 10]], 'a'),
                        ([[0, 0], [0, 10], [10, 10]], 'a'),
                        ]
    # uses outline by default
    test_dataset   = [
                        ((0, 11), settings.DEFAULT_COLOR),  # thickness is 3
                        ((10, 10), settings.DEFAULT_COLOR),
                        ((20, 10), settings.DEFAULT_COLOR),
                        ((4, 4), BACKGROUND),
                        ((100, 1), BACKGROUND),
                        ]
    filled_dataset      = [
                        ((5, 5), settings.DEFAULT_COLOR),
                        ((10, 10), settings.DEFAULT_COLOR),
                        ((9, 9), settings.DEFAULT_COLOR),
                        ((20, 16), BACKGROUND),
                        ((100, 1), BACKGROUND),
                        ]
    shape_class       = drawer.Rectangle

    def test_filled(self):
        im = np.zeros(self.image_shape, np.uint8)
        for coordinates, label in self.valid_dataset:
            shape = self.shape_class(coordinates, label, filled=True)
            shape.draw_on(im)

        for point, value in self.filled_dataset:
            x, y = point
            # notice it is im[y, x] not (x, y)
            self.assertEqual(im[y, x].tolist(), rev(list(value)), "Point(%s, %s) was not drawn." % (x, y))

class RegionRectangleTestCase(RectangleTestCase):
    valid_dataset     = [
                        ([0, 0, 10, 10], 'a'),
                        ([8, 8, 12, 7], 'a')
                        ]
    shape_class       = drawer.Rectangle.from_region


class PointsRectangleTestCase(RectangleTestCase):
    valid_dataset     = [
                        ([[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]], 'a'),
                        ([[8, 8], [20, 8], [20, 15], [8, 15], [8, 8]], 'a')
                        ]
    shape_class       = drawer.Rectangle.from_points


class GeneralPainterTestCase(unittest.TestCase):
    def setUp(self):
        self.image_path = u"tests/sample_data/toolbox/OuNYQbIuF4_00048951.png"
        self.anno_path  = u"tests/sample_data/toolbox/OuNYQbIuF4_00048951.json"

        with open(self.anno_path) as f:
            self.anno_data = json.load(f)

        self.painter = drawer.GeneralPainter(self.image_path)

    def assert_pixel_value(self, im, x, y, value):
        self.assertEqual(im[y, x].tolist(), rev(list(value)), "Point(%s, %s) was not drawn." % (x, y))

    def test_imread(self):
        with self.assertRaises(IOError):
            drawer.GeneralPainter("path/not/existed.jpg")

        p = drawer.GeneralPainter(self.image_path)
        # height, width, depth
        self.assertEqual(p.im.shape, (1080, 1920, 3))

    def test_pallet(self):
        pallet1 = {"label1": 1}
        p1 = drawer.GeneralPainter(self.image_path, pallet=pallet1)
        self.assertEqual(p1._pallet, pallet1)

        pallet2 = {"label2": 2}
        p2 = drawer.GeneralPainter(self.image_path, pallet=pallet2, persistent=True)
        self.assertEqual(p2._pallet, {"label1": 1, "label2": 2})

        pallet3 = {"label2": 3}
        p3 = drawer.GeneralPainter(self.image_path, pallet=pallet3, persistent=True)
        self.assertEqual(p3._pallet, {"label1": 1, "label2": 3})
        self.assertEqual(p1._pallet, {"label1": 1, "label2": 3})

        p4 = drawer.GeneralPainter(self.image_path, persistent=False)
        self.assertEqual(p4._pallet, {})


    @mock.patch("moose.toolbox.image.drawer.colors")
    def test_get_color(self, mock_colors):
        p = drawer.GeneralPainter(self.image_path)
        with self.assertRaises(ImproperlyConfigured):
            p.get_color('label1')

        mock_colors.choice = mock.Mock(return_value=(255, 0, 0))
        p = drawer.GeneralPainter(self.image_path, autofill=True)
        self.assertEqual(p.get_color('label1'), (255, 0, 0))
        mock_colors.choice.assert_called_with(exclude=[])
        self.assertEqual(p._pallet, {'label1': (255, 0, 0)})

        p = drawer.GeneralPainter(self.image_path, autofill=True, use_default=True)
        self.assertEqual(p.get_color('label1'), None)


    def test_render(self):
        self.painter.update_pallet({
                            "label1": (255, 0, 0),
                            "label2": (0, 255, 0),
                            })
        canvas = np.zeros(self.painter.im.shape, np.uint8)
        shape1 = drawer.Rectangle([[0,0], [10,10]], 'label1')
        self.painter.add_shape(shape1)
        self.painter.render(canvas)
        self.assert_pixel_value(canvas, 10, 10, (255, 0, 0))
        self.assert_pixel_value(canvas, 5, 9, (255, 0, 0))
        self.assert_pixel_value(canvas, 5, 5, (0, 0, 0))

        shape2 = drawer.Polygon([[5, 5], [20, 20], [5, 20], [5, 5]], 'label2')
        self.painter.add_shape(shape2)
        self.painter.render(canvas)
        # test if the pixel was reset
        self.assert_pixel_value(canvas, 6, 6, (0, 255, 0))
        self.assert_pixel_value(canvas, 19, 20, (0, 255, 0))
        self.assert_pixel_value(canvas, 4, 10, (255, 0, 0))
