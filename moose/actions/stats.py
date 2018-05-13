# -*- coding: utf-8 -*-
import pprint
import logging

logger = logging.getLogger(__name__)


class StatsCollector(object):

    def __init__(self, action):
        self._dump = action.stats_dump
        self._stats = {}

    def get_value(self, key, default=None, action=None):
        return self._stats.get(key, default)

    def get_stats(self, action=None):
        return self._stats

    def set_value(self, key, value, action=None):
        self._stats[key] = value

    def set_stats(self, stats, action=None):
        self._stats = stats

    def inc_value(self, key, count=1, start=0, action=None):
        d = self._stats
        d[key] = d.setdefault(key, start) + count

    def max_value(self, key, value, action=None):
        self._stats[key] = max(self._stats.setdefault(key, value), value)

    def min_value(self, key, value, action=None):
        self._stats[key] = min(self._stats.setdefault(key, value), value)

    def clear_stats(self, action=None):
        self._stats.clear()

    def open_action(self, action):
        pass

    def close_action(self, action, reason):
        if self._dump:
            logger.info("Dumping Moose stats:\n" + pprint.pformat(self._stats),
                        extra={'action': action})
        self._persist_stats(self._stats, action)

    def _persist_stats(self, stats, action):
        pass


class MemoryStatsCollector(StatsCollector):

    def __init__(self, action):
        super(MemoryStatsCollector, self).__init__(action)
        self.action_stats = {}

    def _persist_stats(self, stats, action):
        self.action_stats[action.name] = stats


class DummyStatsCollector(StatsCollector):

    def get_value(self, key, default=None, action=None):
        return default

    def set_value(self, key, value, action=None):
        pass

    def set_stats(self, stats, action=None):
        pass

    def inc_value(self, key, count=1, start=0, action=None):
        pass

    def max_value(self, key, value, action=None):
        pass

    def min_value(self, key, value, action=None):
        pass
