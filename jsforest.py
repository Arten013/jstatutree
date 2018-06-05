import numpy as np
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing


QSIZE = 1000
class JSTForest(object):
    def __init__(self, proc_count=4, thread_count=5, leaf_etype="Sentence", only_reiki=True):
        self.leaf_etype = leaf_etype
        self.only_reiki = only_reiki
        self.tree_source_dict = OrderedDict()
        self.executor = {
            "process":  ProcessPoolExecutor(self.proc_count),
            "thread":   ThreadPoolExecutor(self.thread_count)
            }

    def executor_deco(executor_type):
        def _executor_deco(func):
            import functools
            @functools.wraps(func)
            def inner(self, queue, *args, **kwargs):
                for arg in args:
                    self.executor[executor_type].submit(func, self, queue, *arg, **kwargs)
                print(func)
                if executor_type is "thread":
                    queue.put(None)
            return inner
        return _executor_deco

    @executor_deco("process")
    @executor_deco("thread")
    def _enqueue_tree_sources_from_path(self, queue, *tree_source_path):
        tree_source = jstatutree.ReikiXMLReader(tree_source_path)
        tree_source.open()
        try:
            tree_source.get_lawdata()
        except:
            print("Failed to get lawdata from xml file")
        tree_source.close()

        if not self.only_reiki or tree_source.lawdata.is_reiki():
            queue.put(tree_source)

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

    def del_tree_source(self, tree_source):
        if tree_source.code in self.tree_source_dict:
            del self.tree_source_dict[tree_source.code]

    @executor_deco("process")
    @executor_deco("thread")
    def _enqueue_leaves(self, queue, *tree_sources):
        for tree_source in tree_sources:
            try:
                for leaf in tree.depth_first_iteration(target=self.leaf_etype):
                    queue.put(leaf)
            except LawError as e:
                print(e)

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