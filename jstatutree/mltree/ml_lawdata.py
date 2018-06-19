import sys, os
import os
import unicodedata
import re
import inspect
import xml.etree.ElementTree as ET
from jstatutree.lawdata import SourceInterface, ReikiData, LawData
from . import ml_etypes
from jstatutree.kvsdict import KVSDict
from time import sleep

def get_text(b, e_val):
    if b is not None and b.text is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

ETYPES = ml_etypes.get_etypes()

class JStatutreeKVS(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.kvsdicts = dict()
        self.kvsdicts["lawdata"] = KVSDict(path=os.path.join(self.path, "lawdata.ldb"))
        self.kvsdicts["root"] = KVSDict(path=os.path.join(self.path, "root.ldb"))
        self.kvsdicts["sentence"] = KVSDict(path=os.path.join(self.path, "sentence.ldb"))

    def close(self):
        for k in list(self.kvsdicts.keys()):
            self.kvsdicts[k].close()
            del self.kvsdicts[k]
        self.kvsdicts = dict()

    def is_closed(self):
        return len(self.kvsdicts) == 0

    def __del__(self):
        if not self.is_closed():
            self.close()

    def __getitem__(self, key):
        return self.kvsdicts[key]

    def set_from_reader(self, reader):
        tree = reader.get_tree()
        code = reader.lawdata.code
        self.kvsdicts["lawdata"][code] = reader.lawdata
        self.kvsdicts["root"][code] = ml_etypes.convert_recursively(tree)
        for e in tree.depth_first_iteration():
            if len(e.text) > 0:
                self.kvsdicts["sentence"][code] = e.text

class KVSReaderBase(SourceInterface):
    def __init__(self, code, db):
        self.code = code
        self.db = db

    def open(self, retry_count=5):
        pass
        """
        err = None
        for _ in range(retry_count):
            try:
                self.db.open()
                return
            except Exception as e:
                sleep(0.1)
                err = e
        raise err
        """

    def close(self):
        pass

    def is_closed(self):
        return self.db is None

    def get_tree(self):
        root = self.db["root"][self.code]
        root.lawdata = self.lawdata
        root.db = self.db
        return root

    def read_lawdata(self):
        #print(self.code, list(self.db["lawdata"].items()))
        return self.db["lawdata"][self.code]

class ReikiKVSReader(KVSReaderBase):
    pass
