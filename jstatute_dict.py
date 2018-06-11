import numpy as np
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
from itertools import combinations
from jstatutree.lawdata import SourceInterface
from jstatutree.kvsdict import KVSDict, KVSPrefixDict
import jstatutree.etypes as etypes


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

class JStatutreeKVSDict(KVSDict):
    DEFAULT_DBNAME = "statutree.ldb"
    PREFIX = "statutree-"

    def __init__(self, path, levels, only_reiki=True, *args, **kwargs):
        self.only_reiki = only_reiki
        self.levels = etypes.sort_etypes(levels)
        super().__init__(path=path, *args, **kwargs)

    def __setitem__(self, key, val):
        assert issubclass(val.__class__, etypes.TreeElement), str(val)+" is not a jstatutree obj."
        if not self.only_reiki or val.lawdata.is_reiki():
            self._set_tree(val, self.levels)

    def _set_tree(self, elem, levels):
        if len(levels) == 0:
            return
        values = []
        for next_elem in elem.depth_first_search(levels[0]):
            values.append(next_elem.code)
            self._set_tree(next_elem, levels[1:])
        if len(values) > 0:
            super().__setitem__(elem.code, values)
        else:
            self._set_tree(elem, _levels[1:])

    def write_batch(self, *args, **kwargs): 
        return JSBatchWriter(self, *args, **kwargs)

class JStatutreeBatchWriter(object):
    def __init__(self, kvsdict, *args, **kwargs):
        self.wb = kvsdict.db.write_batch(*args, **kwargs)
        self._encode_key = kvsdict._encode_key
        self.ENCODING = kvsdict.ENCODING

    def __setitem__(self, key, val):
        assert issubclass(val.__class__, etypes.TreeElement), str(val)+" is not a jstatutree obj."
        if not self.only_reiki or val.lawdata.is_reiki():
            self._set_tree(val, self.levels)

    def _set_tree(self, elem, levels):
        if len(levels) == 0:
            return
        values = []
        for next_elem in elem.depth_first_search(levels[0]):
            values.append(next_elem.code)
            self._set_tree(next_elem, levels[1:])
        if len(values) > 0:
            super().__setitem__(elem.code, values)
        else:
            self._set_tree(elem, _levels[1:])

    def __delitem__(self, key):
        self.wb.delete(self._encode_key(key))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            return False
        self.write()
        return True

    def write(self):
        self.wb.write()

class JSSentenceKVSDict(KVSPrefixDict):
    DEFAULT_DBNAME = "reiki.ldb"
    PREFIX = "sentence-"

    def __init__(self, db, level=None, *args, **kwargs):
        if level is None:
            prefix = self.PREFIX
        else:
            level = level if isinstance(level, str) else level.__name__
            prefix = self.PREFIX + level + "-"
        ret = super().__init__(db=db, prefix=prefix, *args, **kwargs)

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