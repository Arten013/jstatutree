import unittest
import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
import xml_jstatutree as jstatutree
import xml_etypes as etype
from myexceptions import LawError
from concurrent.futures import ProcessPoolExecutor as PPE
from concurrent.futures import ThreadPoolExecutor as TPE
from concurrent.futures import as_completed

import plyvel
import threading
import shutil


files = []
for r, d, f in os.walk(PATH):
    files += f
files = list(set(files))
def find_all_files(directory, extentions=None):
    for root, dirs, files in os.walk(directory):
        if extentions is None or os.path.splitext(root)[1] in extentions:
            yield root
        for file in files:
            if extentions is None or os.path.splitext(file)[1] in extentions:
                yield os.path.join(root, file)

from collections import Counter

def element_counter(path, *args, **kwargs): 
    try:
        rr = jstatutree.ReikiXMLReader(path)
        rr.open()
        tree = rr.get_tree()
        if tree.root is None or not tree.lawdata.is_reiki():
            #print("parse error:", path)
            return Counter()
        return Counter(elems.etype.__name__.encode("utf8") for elems in tree.depth_first_iteration())
    except LawError as e:
        #print(e)
        return Counter()
    except Exception as e:
        print(e)
        print(path)
        return Counter()

def sentence_counter(path, *args, **kwargs):
    try:
        rr = jstatutree.ReikiXMLReader(path)
        rr.open()
        tree = rr.get_tree()
        if tree.root is None or not tree.lawdata.is_reiki():
            #print("parse error:", path)
            return Counter()
        sentences = []
        for u in tree.depth_first_iteration(target=UNIT):
            if u.etype.__name__ != UNIT:
                continue
            s = "".join(u.iter_sentences())
            s = s.encode("utf-8")
            sentences.append(s)
        #print(path)
        return Counter(sentences)
    except LawError as e:
        #print(e)
        return Counter()
    except Exception as e:
        print(e)
        print(path)
        return Counter()

def proc_pref(func, pref_code, *args, **kwargs):
    with TPE(kwargs.get("th_num", 5)) as th:
        futures = [
            th.submit(func, path, *args, **kwargs)
            for path in list(find_all_files(PATH.format(pref_code), [".xml"]))
            ]
    dbname = '{0}_pref{1:02}.ldb'.format(DBBASENAME, pref_code)
    db = plyvel.DB(dbname, create_if_missing=True) 
    print('create db', dbname)
    for f in as_completed(futures):
        for key, value in f.result().items():
            res = db.get(key)
            count = 0 if res is None else int(res)
            db.put(key, bytes(str(count+int(value)).encode("utf8")))
    db.close()
    return dbname

def countfunc_mapper(func, db, *args, **kwargs):
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
            

def count_viewer(counter):
    print(counter)
    for k, v in counter.items():
        print("{0}, {1:,}".format(k, v))

if __name__ == "__main__":
    
    UNIT = "Sentence"
    DBBASENAME = "{}_text_count".format(UNIT.lower())
    base_db = plyvel.DB('{}.ldb'.format(DBBASENAME), create_if_missing=True) 
    
    countfunc_mapper(
        sentence_counter,
        base_db,
        proc_num=4,
        th_num=5,
        )
    """

    DBBASENAME = "element_count"

    base_db = plyvel.DB('{}.ldb'.format(DBBASENAME), create_if_missing=True) 
    
    countfunc_mapper(
        element_counter,
        base_db,
        proc_num=4,
        th_num=5,
        )
    """
    #for i in range(1,100):
    #    sentence_counter("/Users/KazuyaFujioka/Documents/all_data/23/230006/{0:04}.xml".format(i))
    
    for key, value in base_db:
        print(key.decode("utf8"), value)
    base_db.close()

    

