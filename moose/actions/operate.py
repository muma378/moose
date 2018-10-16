# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from moose.toolbox import video
from moose.shortcuts import ivisit
from moose.utils._os import makedirs, makeparents

from .base import AbstractAction, IllegalAction

import logging
logger = logging.getLogger(__name__)


class BaseExtract(AbstractAction):
    """
    Class to simulate the action of extracting frames from
    a video with opencv-python,
    `
    get_context -> lookup_files -> get_extractor -> dump
    `
    while the following steps are implemented by subclasses.

    `parse`
        Get extra info to update context.

    `get_extractor`
        Returns a generator to yield index and frame in each loop

    """

    default_pattern = ('*.mp4', '*.mov', '*.flv', '*.avi')

    def get_context(self, kwargs):
        if kwargs.has_key('config'):
            config = kwargs.get('config')
        else:
            logger.error("Missing argument: 'config'.")
            raise IllegalAction(
                "Missing argument: 'config'. This error is not supposed to happen, "
                "if the action class was called not in command-line, please provide "
                "the argument `config = config_loader._parse()`.")

        context = {
            'root': config.common['root'],
            'relpath': config.common['relpath'] if config.common['relpath'] else config.common['root'],
            'src': config.extract['src']
        }

        context.update(self.parse(config, kwargs))
        return context

    def parse(self, config, kwargs):
        """
        Entry point for subclassed upload actions to update context.
        """
        return {}

    def lookup_files(self, root, context):
        """
        Finds all files located in root which matches the given pattern.
        """
        pattern     = context.get('pattern', self.default_pattern)
        ignorecase  = context.get('ignorecase', True)
        logger.debug("Visit '%s' with pattern: %s..." % (root, pattern))

        files   = []
        for filepath in ivisit(root, pattern=pattern, ignorecase=ignorecase):
            files.append(filepath)
        logger.debug("%d files found." % len(files))
        return files

    def get_extractor(self, context):
        raise NotImplementedError

    def dump(self, extractor, dst, context):
        self.cap.dump(extractor, dst)

    def run(self, **kwargs):
        output = []
        context = self.get_context(kwargs)
        src = context['src']
        files = self.lookup_files(src, context)
        output.append('%d files found to extract frames.' % len(files))
        for video_path in files:
            video_dirname, _ = os.path.splitext(video_path)
            dst = os.path.join(context['root'], os.path.relpath(video_dirname, src))
            if os.path.exists(dst):
                continue
            self.cap = video.VideoCapture(video_path)
            if int(self.cap.fps) != self.cap.fps:
                logger.warning("FPS of %s is %f, not a integer." % (cap.video_name, cap.fps))
            extractor = self.get_extractor(context)
            makedirs(dst)
            self.dump(extractor, dst, context)
        return '\n'.join(output)

class PeriodicExtract(BaseExtract):
    """
    Captures frames in an interval
    """
    def get_extractor(self, context):
        interval = context['step']
        return self.cap.capture(step=interval)

class IndexListExtract(BaseExtract):
    """
    Captures frames as the index list describes
    """
    def get_extractor(self, context):
        idx_list = context['frames']
        return self.cap.extract(idx_list)
