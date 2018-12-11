# -*- coding: utf-8 -*-
# `stats` 模块提供了一个便捷的途径对不同的对象或状态进行计数
# 当Action在初始化的时候自动创建一个stats对象，当需要对某种
# 对象的个数进行统计时，只需要在action内部调用
# `self.stats.inc_value(target_name)` 即可。
#
# 对于target_name，我们建议使用“/”作为域分隔符，比如对于下载
# 结果的统计，我们可以用"download/ok"，"download/http_error"，
# "download/url_error"，"download/unknown" 来表示同一动作
# 下不同结果的个数，在查看日志时可读性也要更好。

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

    def close_action(self, action, identity):
        if self._dump:
            logger.info("Dumping Moose stats:\n" + pprint.pformat(self._stats),
                        extra={'action': action})
        self._persist_stats(self._stats, identity)

    def _persist_stats(self, stats, action):
        pass


class MemoryStatsCollector(StatsCollector):

    def __init__(self, action):
        super(MemoryStatsCollector, self).__init__(action)
        self.action_stats = {}

    def _persist_stats(self, stats, identity):
        self.action_stats[identity] = stats


class SperatedStatsCollector(MemoryStatsCollector):

    def close_action(self, action, identity):
        if self._dump:
            logger.info("Dumping Moose stats:\n" + pprint.pformat(self._stats),
                        extra={'action': action})
        self._persist_stats(self._stats, identity)
        self.clear_stats()


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
