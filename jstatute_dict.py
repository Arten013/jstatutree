import numpy as np
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
from itertools import combinations
from jstatutree import SourceInterface



class JStatuteDict(object):
    def __init__(self, only_reiki=True):
        self.only_reiki = only_reiki
        self.body = dict()

    def __setitem__(self, key, val):
        assert issubclass(val.__class__, SourceInterface), str(val)+" is not a jstatute obj."
        if not self.only_reiki or val.lawdata.is_reiki():
            self.body[key] = val

    def __getitem__(self, key):
        return self.body[key]

    def __len__(self):
        return len(self.body)

"""
QSIZE = 1000
class JSFMultiExecutor(JSForest):
        def __init__():
            self.executor = {
            "process":  ProcessPoolExecutor(self.proc_count),
            "thread":   ThreadPoolExecutor(self.thread_count)
            }

        def executor_deco(executor_type):
        def _executor_deco(func):
            import functools
            @functools.wraps(func)
            def inner(self, queue, *args, **kwargs):
                futures = [
                    self.executor[executor_type].submit(func, self, queue, *arg, **kwargs) for arg in args
                    ]
                for f in as_completed(futures):
                    res = f.result()
                    if res is None:
                        continue
                    else:
                        queue.put(res)
                if executor_type is "thread":
                    queue.put(None)
            return inner
        return _executor_deco

    def add_tree_sources_from_paths(self, *tree_source_paths):
        q = multiprocessing.Queue(QSIZE)
        self._enqueue_tree_sources_from_paths(queue, *tree_source_paths)
        unfinished_thread_count = self.proc_count * self.thread_count
        while unfinished_thread_count > 0:
            item = q.get()
            if item is None:
                unfinished_thread_count -= 1
                continue
            tree_source = item
            self.tree_source_dict[tree_source.code] = tree_source


    def setup_from_basepath(self, basepath):
        self.add_tree_sources_from_paths(find_all_files(basepath, [".xml"]))

    def __iter__(self):
        q = multiprocessing.Queue(QSIZE)
        self._enqueue_leaves(self.tree_source_dict.values())
        unfinished_thread_count = self.proc_count * self.thread_count
        while unfinished_thread_count > 0:
            item = q.get()
            if item is None:
                unfinished_thread_count -= 1
                continue
            leaf = item
            yield leaf
"""