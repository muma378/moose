from __future__ import unicode_literals
import random
from moose.core.exceptions import ImproperlyConfigured

_colors = (
    (0, 255, 0),
    (255, 0, 0),
    (0, 0, 255),
    (255, 102, 102),
    (255, 255, 0),
    (0, 102, 153),
    (255, 153, 102),
    (0, 102, 204),
    (51, 153, 51),
    (255, 204, 51),
    (51, 102, 153),
    (255, 153, 0),
    (255, 255, 204),
    (204, 102, 0),
    (204, 204, 68),
    (153, 204, 51),
    (0, 153, 204),
    (153, 204, 204),
    (0, 100, 100),
    (255, 0, 51),
    (204, 204, 0),
    (51, 204, 153),
    (0, 125, 255),
    (0, 255, 100),
    (0, 51, 200),
    (125, 0, 200),
    (100, 0, 125),
    (51, 0, 153),
    (100, 125, 0),
    (0, 100, 53),
    (153, 0, 102),
    (255, 204, 0),
    (204, 0, 51),
    (51, 51, 153),
    (102, 102, 153),
)

def choice(exclude=None):
    if isinstance(exclude, list) or isinstance(exclude, tuple):
        colors = tuple(set(_colors) - set(exclude))
    else:
        colors = _colors

    if len(colors) == 0:
        raise ImproperlyConfigured("Colors were used up.")

    return random.choice(_colors)
