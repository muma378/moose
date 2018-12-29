# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import copy
from collections import Container

import cv2
import numpy as np
from moose.conf import settings
from moose.utils._os import npath
from moose.core.exceptions import ImproperlyConfigured

from . import colors

import logging
logger = logging.getLogger(__name__)

class InvalidCoordinates(Exception):
	pass

class PaintingFailed(Exception):
	pass

class BaseShape(object):
	"""
	This class represents a shape object, which defines the `coordinates`, `label`,
	`draw_on()` method.

	`coordinates`
		Subclasses defined how to orgnize points to present the shape.

	`label`
		A string indicates the label of the shape object, eg. car, bike, truck etc.

	`options`
		Other params passed to control subclasses' behavor.

		`filled` (default None)
			Whether to use `_outline` or `_fill` to draw shapes on images.

		`color` ()
	"""
	type = None
	default_color = settings.DEFAULT_COLOR
	default_thickness = settings.DEFAULT_THICKNESS
	drawn_filled  = None

	def __init__(self, coordinates, label, **options):
		if self._is_valid_coordinates(coordinates):
			self._coordinates = self.normalize(coordinates)
		else:
			raise InvalidCoordinates("Invalid coordinates for '{}': {}".format(self.type, coordinates))
		self._label  = label
		self._color  = options.get('color', self.default_color)
		self._filled = options.get('filled', self.drawn_filled)
		self._thickness = options.get('thickness', self.default_thickness)
		self._options = options

	def _is_valid_coordinates(self, coordinates):
		return True

	@classmethod
	def _is_list_of_pairs(cls, points):
		"""
		Each point contains a pair of value, which is `x` and `y`
		"""
		if not isinstance(points, Container):
			return False
		for point in points:
			if not (cls.is_valid_format(point) and cls.is_valid_value(point)):
				return False
		return True

	@classmethod
	def is_valid_format(cls, point):
		# type of list or tuple, and the length is 2
		return (isinstance(point, list) or isinstance(point, tuple)) \
			and len(point) == 2

	@classmethod
	def is_valid_value(cls, point):
		# assume the format is correct
		x, y = point

		# type conversion is allowed
		try:
			x, y = int(x), int(y)
		except ValueError as e:
			return False

		# must be a postive value
		return x >= 0 and y >= 0


	def normalize(self, coordinates):
		norm_coordinates = []
		for coord in coordinates:
			# to convert float to int and list to tuple
			norm_coordinates.append((int(coord[0]), int(coord[1])))
		return norm_coordinates

	@classmethod
	def _equal_points(cls, p1, p2):
		return p1[0] == p2[0] and p1[1] == p2[1]

	def set_color(self, color):
		# do not change the default color when `color` set was None
		if color != None:
			self._color = color
		return self

	@property
	def color(self):
		"""
		Note that (R, G, B) was reversed in OpenCV, meanwhile the color
		was a integer when the canvas was a grayscale image.
		"""
		if isinstance(self._color, list) or isinstance(self._color, tuple):
			return self._color[::-1]
		else:
			return self._color

	def draw_on(self, im):
		"""
		Defines the default behavior when shapes were to draw on an image.
		"""
		if self._filled:
			self._fill(im)
		else:
			self._outline(im)

	def _fill(self, im):
		"""
		Fills the shape with colors on the image, it is allowed to raise an error
		if the shape was not closed.
		"""
		raise NotImplementedError("%s does not provide method `fill()`" % self.__class__.__name__)

	def _outline(self, im):
		"""
		Draws the outline of the shape, would be the default drawing behavior when
		shape was not closed.
		"""
		raise NotImplementedError("%s does not provide method `outline()`" % self.__class__.__name__)


class Point(BaseShape):
	"""
	`coordinates`:
		[x, y]
	"""
	type = "Point"
	radius = settings.DRAWER_RADIUS

	def _is_valid_coordinates(self, coordinates):
		if self._is_list_of_pairs([coordinates]):
			return True
		else:
			return False

	def normalize(self, coord):
		return (int(coord[0]), int(coord[1]))

	def draw_on(self, im):
		# let thickness be a negative value to fill the circle
		cv2.circle(im, self._coordinates, self.radius, self.color, -1)

class LineString(BaseShape):
	"""
	`coordinates`:
		[[x0, y0], [x1, y1]]
		[[x0, y0], [x1, y1], [x2, y2]]
	"""
	type = "LineString"

	def _is_valid_coordinates(self, coordinates):
		if self._is_list_of_pairs(coordinates) and len(coordinates) >= 2:
			return True
		else:
			return False

	def draw_on(self, im):
		for start, end in zip(self._coordinates[:-1], self._coordinates[1:]):
			cv2.line(im, start, end, self.color, self._thickness)


class Polygon(BaseShape):
	"""
	`coordinates`:
		[[x1, y1], [x2, y2] ... [xn, yn], [x1, y1]]
	"""
	type = "Polygon"
	is_closed    = False
	drawn_filled = True

	def _is_valid_coordinates(self, coordinates):
		if self._is_list_of_pairs(coordinates) and len(coordinates) > 2 and \
			self._equal_points(coordinates[0], coordinates[-1]):
			return True
		else:
			return False

	def to_nparray(self):
		return np.array(self._coordinates, np.int32)

	def _fill(self, im):
		cv2.fillPoly(im, [self.to_nparray()], self.color)

	def _outline(self, im):
		cv2.polylines(im, [self.to_nparray()], self.is_closed, self.color, self._thickness)


class Rectangle(BaseShape):
	"""
	`coordinates`:
		Default  : [[x1, y1], [x2, y2]]

		from_region: [x, y, w, h]
		from_points: [[x1, y1], [x1, y2], [x2, y2,], [x2, y1], [x1, y1]]
	"""
	type = "Rectangle"
	drawn_filled = False

	def _is_valid_coordinates(self, coordinates):
		if self._is_list_of_pairs(coordinates) and len(coordinates) == 2:
			return True
		else:
			return False

	@classmethod
	def from_region(cls, region, label, **options):
		if isinstance(region, Container) and len(region) == 4:
			x, y, w, h = region
			return cls([(x, y), (x+w, y+h)], label, **options)
		else:
			raise InvalidCoordinates()

	@classmethod
	def from_points(cls, points, label, **options):
		if cls._is_list_of_pairs(points) and len(points)==5 and \
			cls._equal_points(points[0], points[-1]):
			coordinates = [points[0], points[2]]
		else:
			raise InvalidCoordinates()
		return cls(coordinates, label, **options)

	def to_points(self):
		x1, y1 = self._coordinates[0]
		x2, y2 = self._coordinates[1]
		return [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]

	def _outline(self, im):
		cv2.rectangle(im, tuple(self._coordinates[0]), tuple(self._coordinates[1]), self.color, self._thickness)

	def _fill(self, im):
		cv2.rectangle(im, tuple(self._coordinates[0]), tuple(self._coordinates[1]), self.color, -1)


class GeneralPainter(object):
	"""
	在绘图的颜色选择上有三种可能:

		1. () 用户提供完整的pallet，包含每一个可能的label和color，如果缺失则报错；
		2. (use_default=True) 用户没有提供pallet，全部统一使用一种颜色来填充；
		3. (use_default=True), Shape(color=c) 用户没有提供pallet，每种shape使用一种颜色填充(可以与2归为一种情况)；
		4. (autofill=True, use_default=False) 用户提供不完整的或没有提供pallet，缺失的使用随机颜色来填充，但每个label必须是唯一的；
	"""

	shape_line_cls      = LineString
	shape_point_cls     = Point
	shape_polygon_cls   = Polygon
	shape_rectangle_cls = Rectangle
	persistent_pallet   = {}

	def __init__(self, image_path, pallet=None, autofill=False, use_default=False, persistent=True):
		if not os.path.exists(image_path):
			logger.warning("Unable to find the image specified: {}".format(image_path))
			raise IOError("Unable to find the image specified: {}".format(image_path))
		self.image_path = image_path
		self.im = cv2.imread(npath(image_path))
		# add colors automatically
		self._autofill = autofill
		self._use_default = use_default
		self._persistent  = persistent
		# reset pallet if not set persistent True
		self._pallet = self.persistent_pallet if persistent else {}
		# update pallet if a new one was given
		if pallet:
			self.update_pallet(pallet)
		self._shapes      = []

	def get_color(self, label):
		if self._use_default:
			return None

		if self._pallet.get(label) == None:
			if self._autofill:
				# dict.values() returns a iterator, uses list() to force convert
				color = colors.choice(exclude=list(self._pallet.values()))
				self.add_color(label, color)
			else:
				raise ImproperlyConfigured("Color for lable '{}' was not set.".format(label))

		return self._pallet[label]

	def add_color(self, label, color):
		self._pallet[label] = color

	def update_pallet(self, pallet):
		if isinstance(pallet, dict):
			self._pallet.update(pallet)
		else:
			raise ImproperlyConfigured("`Pallet` must be a type 'dict'")

	def add_shape(self, shape):
		# A shape object must provide attribute `label` and method `draw_on`
		self._shapes.append(shape)

	def from_shapes(self, shapes):
		# `shapes` may be a generator
		self._shapes.extend(list(shapes))

	def clear(self):
		self._shapes = []

	def add_line(self, p1, p2, label, **options):
		shape = self.shape_line_cls([p1, p2], label, **options)
		self.add_shape(shape)

	def add_point(self, p, lable, **options):
		shape = self.shape_point_cls(p, label, **options)
		self.add_shape(shape)

	def add_rectangle(self, p1, p2, lable, **options):
		shape = self.shape_rectangle_cls([p1, p2], label, **options)
		self.add_shape(shape)

	def add_polygon(self, pts, label, **options):
		shape = self.shape_polygon_cls(pts, label, **options)
		self.add_shape(shape)

	def render(self, canvas):
		for shape in self._shapes:
			shape.set_color(self.get_color(shape._label))
			shape.draw_on(canvas)
		return canvas

	def draw(self, filename):
		# Do not draw on the original image
		img = copy.deepcopy(self.im)
		img = self.render(img)
		cv2.imwrite(npath(filename), img)

	def masking(self, filename):
		mask = np.zeros(self.im.shape, np.uint8)
		mask = self.render(mask)
		cv2.imwrite(npath(filename), mask)

	# More detailes on addWeighted
	# http://www.opencv.org.cn/opencvdoc/2.3.2/html/doc/tutorials/core/adding_images/adding_images.html
	def blend(self, filename, alpha=0.7, gamma=0.0):
		if alpha < 1.0 and alpha > 0.0:
			beta = 1.0 - alpha
		else:
			raise PaintingFailed("Parameter `alpha` is ought to be in the range of 0 and 1.0")
		mask = np.zeros(self.im.shape, np.uint8)
		mask = self.render(mask)
		blended_img = cv2.addWeighted(self.im, alpha, mask, beta, gamma)
		cv2.imwrite(npath(filename), blended_img)


class GeoJSONPainter(GeneralPainter):

	def from_features(self, features):
		return self
