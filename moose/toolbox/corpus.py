# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import random
import pickle
import hashlib

from moose.shortcuts import ivisit
from moose.utils._os import makedirs, makeparents
from moose.utils.module_loading import import_string

import logging
logger = logging.getLogger(__name__)

class CorpusFacotory(object):
    group_prefix = 'G'
    group_ndigit = 4

    def __init__(self, feeder_cls, maker_cls, cache_path):
        self.feeder_cls = import_string(feeder_cls)
        # self.maker_cls  = import_string(maker_cls)
        self.cache_path = cache_path

    def feed(self, pool_cls_str, topics_options):
        self.topics_options = topics_options
        feeder = self.feeder_cls.create_from_options(pool_cls_str, self.topics_options, self.cache_path)
        self.pools  = feeder.get_pools()

    def concat(self, old_lines_coll, new_lines_coll):
        for old_lines, new_lines in zip(old_lines_coll, new_lines_coll):
            old_lines.extend(new_lines)
        return old_lines_coll

    def make(self, iteration):
        lines_coll = [list() for _ in range(iteration)]
        for option in self.topics_options:
            topic, path, proportion, repeat = option
            topic_lines = self.pools[topic].allocate(proportion, iteration)
            self.concat(lines_coll, topic_lines)
            self.pools[topic].dump()
        return lines_coll

    def write(self, groups, start, dst):
        makedirs(dst)
        for i, group in enumerate(groups):
            group_id = self.group_prefix + str(start+i).zfill(self.group_ndigit)
            group_text = os.path.join(dst, group_id+'.txt')
            with open(group_text, 'w') as f:
                for i, corpus in enumerate(group, start=1):
                    f.write(u"{}\t{}\n".format('S'+str(i).zfill(4), corpus.content).encode('utf-8'))


class CorpusGroup(object):
    pass


class Corpus(object):
    def __init__(self, content, nref=0, tags=None):
        self.content = content
        self.nref    = nref
        self.tags    = tags

    def get_md5(self):
        return hashlib.md5(self.content.encode('utf-8')).hexdigest()

    def add_tag(self, tag):
        if isinstance(self.tags, list):
            self.tags.append(tag)

    def incr_ref(self):
        self.nref += 1


class CorpusPool(object):
    def __init__(self, topic, max_repeat, cache_path=None):
        self.topic = topic
        self.max_repeat = max_repeat
        self.cache_path = os.path.join(cache_path, topic)
        self.pool_table  = self.load(self.cache_path)

    def dump(self):
        makeparents(self.cache_path)
        with open(self.cache_path, 'w') as f:
            pickle.dump(self.pool_table, f)

    def load(self, cache_path):
        pool = {}
        if self.topic != 'composition' and os.path.exists(cache_path):
            with open(cache_path) as f:
                pool = pickle.load(f)
        return pool

    def feed(self, content, nref=0, tags=None):
        self.add(Corpus(content, nref, tags))

    def add(self, corpus):
        if isinstance(corpus, Corpus):
            signature = corpus.get_md5()
            if not self.pool_table.has_key(signature):
                self.pool_table[signature] = corpus
            else:
                logger.warning("Replicated corpus found: '{}'".format(corpus.content))
        else:
            raise ValueError("Target to add is an instance of 'Corpus'.")

    def get_available_pool(self, least_amount):
        self.pool = self.pool_table.values()
        if self.max_repeat == -1:
            return self.pool

        # removes corpus exceeds the max used times
        self.pool = filter(lambda x: x.nref<self.max_repeat, self.pool)
        repeat_times = 0
        available_pool = []
        # prefer to use the corpus with least-used-times
        while repeat_times < self.max_repeat:
            available_pool.extend(filter(lambda x: x.nref==repeat_times, self.pool))
            if len(available_pool) >= least_amount:
                return available_pool
            repeat_times += 1
        logger.error(
            ("Text for topic '{}' has {} items in total, "
            "not enough for assembling.").format(self.topic, len(self.pool)))
        raise ValueError("Text not enough for assembling.")

    def allocate(self, nline, iteration=1):
        lines = []
        while iteration:
            available_pool = self.get_available_pool(nline)
            if self.topic == 'baidu':
                # not shuffled
                allocated = available_pool
            else:
                allocated = random.sample(available_pool, nline)
            self.update(allocated)
            lines.append(allocated)
            iteration -= 1
        return lines

    def update(self, lines):
        for corpus in lines:
            corpus.incr_ref()


class TopicsFeeder(object):
    def __init__(self, topics_repeat_table, pool_cls, cache_path):
        self.pools = {t: pool_cls(t, n, cache_path) for t,n in topics_repeat_table.items()}

    def get_pools(self):
        return self.pools

    @classmethod
    def create_from_options(cls, pool_cls_str, options, cache_path):
        topics_repeat_table = {o[0]:o[-1] for o in options}
        pool_cls      = import_string(pool_cls_str)
        topics_feeder = cls(topics_repeat_table, pool_cls, cache_path)

        for option in options:
            topic, path, proportion, repeat = option
            topics_feeder.feed(topic, path)

        return topics_feeder

    def visit(self, path):
        if os.path.isdir(path):
            for filepath in ivisit(path, pattern='*.txt'):
                yield filepath
        elif os.path.isfile(path):
            yield path
        else:
            logger.error("Files not found: '{}'".format(path))
            raise IOError("Files not found: '{}'".format(path))

    def feed(self, topic, path):
        if self.pools.has_key(topic):
            topic_pool = self.pools[topic]
        else:
            logger.error("Topic '{}' not declared in context.".format(topic))
            raise ValueError("Topic '{}' not declared in context.".format(topic))

        for filepath in self.visit(path):
            with open(filepath) as f:
                for line in f:
                    line = line.strip().decode('utf-8')
                    topic_pool.feed(line)
