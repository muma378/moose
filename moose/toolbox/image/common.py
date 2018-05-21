# -*- coding: utf-8 -*-

from PIL import Image


def image_size(image_path):
    im = Image.open(image_path)
    return im.width, im.height


class BoundingBoxError(Exception):
	"""
	return error code and message, meanwhile modified result if possible
	"""
	SERIOUS = 1
	WARNING = 2
	TRIVIAL = 3

	def __init__(self, code, message, suggest):
		super(BoundingBoxError, self).__init__()
		self.code = code
		self.message = message
		self.suggest = suggest

	def __str__(self):
		return self.message

# ensure x1 < x2 and y1 < y2
# while (x1, y1, x2, y2) = region
def normalize(region, width=None, height=None, level=BoundingBoxError.SERIOUS):
	xmin, ymin, xmax, ymax = region

	# no idea what the possible value is
	if xmin == xmax or ymin == ymax:
		raise BoundingBoxError(BoundingBoxError.SERIOUS, "points given are overlapped", None)

	if width and height:
		if min(xmin, xmax) > width or min(ymin, ymax) > height:
			raise BoundingBoxError(BoundingBoxError.SERIOUS, "xmin or ymin is out of boundary", None)
	
	msgs = []
	# common cases, just flip
	if xmin > xmax:
		xmax, xmin = xmin, xmax
		msgs.append("coordinate along x-axis is upside down")
	if ymin > ymax:
		ymax, ymin = ymin, ymax
		msgs.append("coordinate along y-axis is upside down")
	if xmin < 0:
		xmin = 0
		msgs.append("xmin is less than 0")
	if ymin < 0:
		ymin = 0
		msgs.append("ymin is less than 0")

	if msgs and level >= BoundingBoxError.TRIVIAL:
		raise BoundingBoxError(BoundingBoxError.TRIVIAL, '; '.join(msgs), (xmin, ymin, xmax, ymax))

	# maybe we shall not pass the boundray?
	if width:
		if xmax >= width:
			xmax = width - 1
			msgs.append("horizontal bar of bounding box is outside the boundary")
	if height:
		if ymax >= height:
			ymax = height - 1
			msgs.append("vertical bar of bounding box is outside the boundary")

	if msgs and level >= BoundingBoxError.WARNING:
		raise BoundingBoxError(BoundingBoxError.WARNING, '; '.join(msgs), (xmin, ymin, width, ymax))
	
	return (int(xmin), int(ymin), int(xmax), int(ymax))
