# -*- coding: utf-8 -*-
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moose.utils._os import npath
from .pallet import dip, create_pallet


# point = (x1, y1)
def draw_points(img_name, dst_name, points, fill=128):
	im = Image.open(img_name)
	draw = ImageDraw.Draw(im)
	draw.point(points, fill)
	font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 15)
	for i, point in enumerate(points):
		draw.text(point, str(i), font=font)
	im.save(dst_name)


# point = (x1, y1)
def draw_circles(img_name, dst_name, points):
	img = cv2.imread(npath(img_name))
	font = cv2.FONT_HERSHEY_SIMPLEX
	for i, point in enumerate(points):
		img = cv2.circle(img, point, 3, (0,255,0), -1)
		img = cv2.putText(img, str(i), point, font, 0.5, (255,255,255,50), 1, cv2.LINE_AA)
	cv2.imwrite(npath(dst_name), img)


# region = (x1, y1, x2, y2)
def draw_rectangles(img_name, dst_name, datalist, pallet=None):
	if not pallet:
		pallet = create_pallet(datalist, is_global=True)

	im = Image.open(img_name)
	draw = ImageDraw.Draw(im)
	for label, region in datalist:
		draw.rectangle(region, outline=pallet[label])

	im.save(dst_name)


def draw_polygons(img_name, dst_name, datalist, pallet=None, border=False, grayscale=False):
	"""
	Draws a mask on a black background.

	`img_name`
		source file path

	`dst_name`
		dstination file path

	`datalist`
		a tuple of two-element-tuple contains `label` and `points`, such as "(
		("label1", [[x1, y1], [x2, y2] ... [xn, yn]]),
		("label2", [[x1, y1], [x2, y2] ... [xn, yn]]),
		)"

	`pallet`
		a dict represents label and corresponding color to draw, such as "{
		'label1': (255, 0, 0),
		'label2': (0, 255, 0),
		}
		"

	`border`
		False or a tuple indicating the color to use (such as `(255, 255, 255)`)

	`grayscale`
		a boolean indicates whether the image was grayscale or rgb
	"""
	image = cv2.imread(npath(img_name))

	# constructs the pallet if not defined before
	if not pallet:
		labels = set()
		for label, _ in datalist:
			labels.add(label)

		nlabel = len(labels)
		if grayscale:
			colors = range(0, 256, 256/nlabel)[1:]	# do not use color black
			pallet = {k: v for k, v in zip(list(labels), colors)}
		else:
			pallet = create_pallet(datalist, is_global=True)

	default = pallet.get('default', None)

	# constructs a canvas with different storage ability: 8 or 24 bit/pixel
	if grayscale:
		canvas = np.zeros(image.shape[:2]+(1, ), np.uint8)
	else:
		canvas = np.zeros(image.shape, np.uint8)

	# draw
	for label, points in datalist:
		pts = np.array(points, np.int32)
		if border:
			cv2.polylines(canvas, [pts], True, border, 3)
		cv2.fillPoly(canvas, [pts], (pallet.get(label, default)))

	cv2.imwrite(npath(dst_name), canvas)
	return pallet


def blend(img_name, dst_name, datalist, pallet=None, alpha=0.4, beta=0.6):
	"""
	Blends the raw image with a mask which segmented according to the datalist.

	`img_name`
		source file path

	`dst_name`
		dstination file path

	`datalist`
		a tuple of two-element-tuple contains `label` and `points`, such as "(
		("label1", [[x1, y1], [x2, y2] ... [xn, yn]]),
		("label2", [[x1, y1], [x2, y2] ... [xn, yn]]),
		)"

	`pallet`
		a dict represents label and corresponding color to draw, such as "{
		'label1': (255, 0, 0),
		'label2': (0, 255, 0),
		}
		"

	`alpha, beta`
		weights for the proportion of raw image and mask
	"""
	image = cv2.imread(npath(img_name))

	# constructs the pallet if not defined before
	if not pallet:
		pallet = create_pallet(datalist, is_global=True)

	default = pallet.get('default', None)

	# draw
	mask = np.zeros(image.shape, np.uint8)
	for label, points in datalist:
		pts = np.array(points, np.int32)
		cv2.fillPoly(mask, [pts], (pallet.get(label, default)))

	blended = cv2.addWeighted(image, alpha, mask, beta, 0)
	cv2.imwrite(npath(dst_name), blended)
	return pallet
