# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import copy

import cv2
import numpy as np
from moose.conf import settings
from moose.utils._os import npath

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
	"""
	type = None
	default_color = settings.DEFAULT_COLOR
	thickness     = settings.DEFAULT_THICKNESS

	def __init__(self, coordinates, label, **options):
		if self._is_valid_coordinates(coordinates):
			self._coordinates = self.normalize(coordinates)
		else:
			raise InvalidCoordinates("Invalid coordinates for '{}': {}".format(self.type, coordinates))
		self._label = label
		self._color = options.get('color', self.default_color)
		self._options = options

	def _is_valid_coordinates(self, coordinates):
		return True

	def _is_list_of_pairs(self, points):
		"""
		Each point contains a pair of value, which is `x` and `y`
		"""
		# TODO: check if elements in point are digital
		for point in points:
			if len(point) != 2 :
				return False
		return True

	def normalize(self, coordinates):
		norm_coordinates = []
		for coord in coordinates:
			# to convert float to int and list to tuple
			norm_coordinates.append((int(coord[0]), int(coord[1])))
		return norm_coordinates

	@classmethod
	def _equal_point(cls, p1, p2):
		return p1[0] == p2[0] and p1[1] == p2[1]

	def set_color(self, color):
		self._color = color
		return self

	def draw_on(self, im):
		"""
		Defines the default behavior when shapes were to draw on an image.
		"""
		if self._options.get('filled'):
			self._fill(im)
		else:
			self._outline(im)

	def _fill(self, im):
		"""
		Fills the shape with colors on the image, it is allowed to raise an error
		if the shape was not a closure.
		"""
		raise NotImplementedError("%s does not provide method `fill()`" % self.__class__.__name__)

	def _outline(self, im):
		"""
		Draws an outline of the shape, -·
		"""
		raise NotImplementedError("%s does not provide method `outline()`" % self.__class__.__name__)


class LineString(BaseShape):
	"""
	`coordinates`:
		[[x0, y0], [x1, y1]]
	"""
	type = "LineString"

	def is_valid_coordinates(self, coordinates):
		if len(coordinates) == 2:
			if self._is_list_of_pairs(coordinates):
				return True
		else:
			return False

	def draw_on(self, im):
		cv2.line(im, self._coordinates[0], self._coordinates[1], self._color, self.thickness)


class Point(BaseShape):
	"""
	`coordinates`:
		[x, y]
	"""
	type = "Point"
	radius = settings.DRAWER_RADIUS

	def is_valid_coordinates(self, coordinates):
		if self._is_list_of_pairs([coordinates]):
			return True
		else:
			return False

	def normalize(self, coord):
		return [int(coord[0]), int(coord[1])]

	def draw_on(self, im):
		cv2.circle(im, self._coordinates, self._color, self.radius)


class Polygon(BaseShape):
	"""
	`coordinates`:
		[[x1, y1], [x2, y2] ... [xn, yn], [x1, y1]]
	"""
	type = "Polygon"
	is_closed = False

	def is_valid_coordinates(self, coordinates):
		if len(coordinates) > 2 and self._is_list_of_pairs(coordinates) and \
			self._equal_points(self, coordinates[0], coordinates[1]):
			return True
		else:
			return False

	def _fill(self, im):
		cv2.fillPoly(im, [self._coordinates], self._color)

	def _outline(self, im):
		cv2.polylines(im, [self._coordinates], self.is_closed, self._color, self.thickness)



class Rectangle(BaseShape):
	"""
	`coordinates`:
		Pair  : [[x1, y1], [x2, y2]]
		Region: [x, y, w, h]
		Points: [[x1, y1], [x1, y2], [x2, y2,], [x2, y1], [x1, y1]]
	"""
	type = "Rectangle"

	# TODO: a straight forward logic
	def _normalize_coordinates(self, coordinates):
		"""
		Converts all kinds of formats to [[x1, y1], [x2, y2]]
		"""
		if len(coordinates) == 4:
			if self._is_list_of_pairs(coordinates):
				return self.from_points(coordinates)
			else:
				return self.from_region(coordinates)
		elif len(coordinates) == 5:
			return self.from_points(coordinates)
		elif len(coordinates) == 2 and self._is_list_of_pairs(coordinates):
			return coordinates
		else:
			raise InvalidCoordinates()

	def _is_valid_coordinates(self, coordinates):
		if len(coordinates) == 2:
			if self._is_list_of_pairs(coordinates):
				return True
		else:
			return False

	@classmethod
	def from_region(cls, region, label, **options):
		if len(region) == 4:
			x, y, w, h = region
			return cls([(x, y), (x+w, y+h)], label, **options)
		else:
			raise InvalidCoordinates()

	@classmethod
	def from_points(cls, points, label, **options):
		if len(points) == 4:
			coordinates = [points[0], points[2]]
		elif len(points) == 5 and cls._equal_point(points[0], points[-1]):
			coordinates = [points[0], points[2]]
		else:
			raise InvalidCoordinates()
		return cls(coordinates, label, **options)

	def to_points(self):
		x1, y1 = self._coordinates[0]
		x2, y2 = self._coordinates[1]
		return [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]

	def _outline(self, im):
		cv2.rectangle(im, tuple(self._coordinates[0]), tuple(self._coordinates[1]), self._color, self.thickness)

	def _fill(self, im):
		cv2.rectangle(im, tuple(self._coordinates[0]), tuple(self._coordinates[1]), self._color, -1)



class GeneralPainter(object):
	shape_line_cls      = LineString
	shape_point_cls     = Point
	shape_polygon_cls   = Polygon
	shape_rectangle_cls = Rectangle
	ignore_errors       = True

	def __init__(self, image_path):
		self.image_path = image_path
		self.im = cv2.imread(npath(image_path))
		self._shapes = []
		self._pallet = None

	def set_pallet(self, pallet):
		self._pallet = pallet

	def add_shape(self, shape):
		# A shape object must provide attribute `label` and method `draw_on`
		self._shapes.append(shape)

	def from_shapes(self, shapes):
		# `shapes` may be a generator
		self._shapes.extend(list(shapes))

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

	def from_features(self, shapes):
		return self
