# -*- coding: utf-8 -*-

from PIL import Image


def image_size(image_path):
    im = Image.open(image_path)
    return im.width, im.height
