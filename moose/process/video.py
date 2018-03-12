# -*- coding: utf-8 -*-

import os
import sys

import cv2
import numpy as np

from moose.utils._os import npath


# (100, 3) -> [99, 101, 98, 102, 97, 103]
def find_n_nearest(i, n):
	for shift in range(n):
		yield i - shift
		yield i + shift


class VideoCapture(object):
	"""
	VideoCapture is a class to ease the use of extracting frames from a video

	"""

	extension_allowed = ('.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG')

	def __init__(self, video_path):
		if not os.path.exists(video_path):
			raise IOError("No such file or directory: %s" % video_path)

		self.video_name = os.path.basename(video_path)
		self.cap = cv2.VideoCapture(npath(video_path))
		self.nframes = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
		self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
		self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
		self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
		self.seconds = self.nframes/self.fps + (1 if self.nframes%self.fps > 0 else 0)

	# captures a series of pictures from `start` to `end`-1 with interval `step`
	# the images captures was name as `name_format`, if it was not given,
	# outputs as the default style.
	def capture(self, start=None, end=None, step=1, find_neighbour=False):
		# captures from [n, n+step, n+2*step, ..., end-1]

		if start == None:
			start = 0
		if end == None:
			end = self.nframes
		if start < 0 or end > self.nframes:
			raise ValueError("The frames (%d, %d) to capture is out of the range." % (start, end))

		corrupt_frames = []
		for idx in range(start, end, step):
			ret, frame = self.retrieve(idx)
			# TODO: when `ret` was false but not retrive in sequence,
			# reads the previous or next one instead
			if ret:
				yield (idx, frame)
			else:
				print("Frame '%d' is corrupt." % idx)
				corrupt_frames.append(idx)
				# find the nearest one but in the range of interval
				if find_neighbour and step != 1:
					for neighbour_idx in find_n_nearest(idx, step):
						ret, frame = self.retrieve(neighbour_idx)
						if ret:
							print("Frame '%d' is substitute for the frame '%d'" % (neighbour_idx, idx))
							yield (neighbour_idx, frame)
							break

		yield (-1, corrupt_frames)

	# idx_list is a list consist of integer which indicates the
	def extract(self, idx_list, find_neighbour=False):
		if min(idx_list) < 0:
			raise ValueError("The frames %d to extract is out of the range." % min(idx_list))
		if max(idx_list) > self.nframes:
			raise ValueError("The frames %d to extract is out of the range." % max(idx_list))

		corrupt_frames = []
		for idx in idx_list:
			ret, frame = self.retrieve(idx)
			# TODO: when `ret` was false but not retrive in sequence,
			# reads the previous or next one instead
			if ret:
				yield (idx, frame)
			else:
				print("Frame '%d' is corrupt." % idx)
				corrupt_frames.append(idx)
				# find the nearest one but in the range of interval
				if find_neighbour:
					step = 1 	# finds the frame which in the distant of 1
					for neighbour_idx in find_n_nearest(idx, step):
						ret, frame = self.retrieve(neighbour_idx)
						if ret:
							print("Frame '%d' is substitute for the frame '%d'" % (neighbour_idx, idx))
							yield (neighbour_idx, frame)
							break

			yield (-1, corrupt_frames)

	# writes all frames returned by extracter to dst_path with given name format
	# extracter is an iterator to yield the idx and frame retrieved frome the video
	# if idx was -1, the frame returned was the list of corrupt frames idx
	def dump(self, extracter, dst_path, name_format=None, ext="jpg"):
		# ext provided should be starts with '.'
		if ext and not ext.startswith("."):
			ext = '.' + ext

		if ext not in self.extension_allowed:
			raise ValueError("Invalid extension '%s' for image." % ext)

		# default naming format: abc.avi -> abc%03d.jpg (if abc.avi has hundreds frames)
		if not name_format:
			name, _ = os.path.splitext(self.video_name)
			ndigit = len(str(self.nframes))
			name_format = name + '_f%0' + str(ndigit) + 'd' + ext
			print("Use the default format '%s'." % name_format)


		if not os.path.isdir(dst_path):
			os.makedirs(dst_path)

		dst_file_format = os.path.join(dst_path, name_format)

		# retrieves idx and frame from the extracter
		for idx, frame in extracter:
			if idx >= 0:
				dst_file = dst_file_format % idx
				self.write(frame, dst_file)

		# if the loop was ended correctly, which means the last statement
		# (yield (-1, frame)) was executed at last
		if idx == -1:
			return frame
		else:
			print("VideoCapture was ended incorrectly")


	def write(self, frame, dst_file):
		if os.path.exists(dst_file):
			raise IOError("File is already existed.")

		cv2.imwrite(npath(dst_file), frame)


	# extracts a frame from the video, value to return is a tuple of (ret, frame)
	# ret is a boolean to indicate the frame was read correctely or not
	def retrieve(self, idx):
		if not isinstance(idx, int):
			raise ValueError("The frame id to retrieve should be integer.")

		if idx >= self.nframes or idx < 0:
			raise ValueError("The frame to retrieve is out of the range.")

		self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
		return self.cap.read()
