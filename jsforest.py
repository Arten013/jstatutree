import numpy as np

class JSTForest(object):
    def __init__(self, basepath, leaf_etype="Sentence", only_reiki=True):
        self.basepath = basepath
        self.leaf_etype = leaf_etype
        self.only_reiki = only_reiki
        self.init_tree_source_dict()

        for path in list(find_all_files(self.basepath, [".xml"])):
            reiki_reader = jstatutree.ReikiXMLReader(path)
            self.tree_source_dict[reiki_reader.code] = reiki_reader

    def __iter__(self):
        if self.proccount
        for tree_code, tree_source in self.tree_source_dict.items():
            try:
                tree_source.open()
            except Exception as e:
                print(e)
                print(tree_source.path)
                del self.tree_source_dict[tree_code]
                continue
            if self.only_reiki and not tree_source.lawdata.is_reiki():
                del self.tree_source_dict[tree_code]
                continue
            try:
                yield tree_source.get_tree()
                tree_source.close()
        proc_num = kwargs.get("proc_num", 4)
        if proc_num > 0:
            with PPE(proc_num) as proc:
                futures = [
                    proc.submit(proc_pref, func, pref_code, *args, **kwargs)
                    for pref_code in range(1,48)
                    ]
            for f in as_completed(futures):
                source_db_name = f.result()
                source_db = plyvel.DB(source_db_name, create_if_missing=False)
                for key, value in source_db:
                    res = db.get(key)
                    count = 0 if res is None else int(res)
                    db.put(key, bytes(str(count+int(value)).encode("utf8")))
                source_db.close()
                #shutil.rmtree(source_db_name)
        else:
            for pref_code in range(1,48):
                source_db_name = proc_pref(func, pref_code, *args, **kwargs)
                source_db = plyvel.DB(source_db_name, create_if_missing=False)
                for key, value in source_db:
                    res = db.get(key)
                    count = 0 if res is None else int(res)
                    db.put(key, bytes(str(count+int(value)).encode("utf8")))
                source_db.close()

class JSTForestDataset(JSTForest):
    def iter_leaf(self):
        for tree in self:
            try:
                for u in tree.depth_first_iteration(target=self.leaf_etype):
                    if u.etype.__name__ != self.leaf_etype:
                        continue
                    yield "".join(u.iter_sentences())
            except LawError as e:
                print(e)