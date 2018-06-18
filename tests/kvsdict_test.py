import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
from jstatutree.kvsdict import KVSDict, KVSPrefixDict
import unittest
import shutil
import time

TEST_PATH = os.path.dirname(__file__)
DB_PATH = os.path.join(TEST_PATH, "testdb.ldb")
class KVSDictTestCase(unittest.TestCase):
    def setUp(self):
        self.kvsdict = KVSDict(path=DB_PATH, create_if_missing=True)
        self.pfdict = KVSPrefixDict(self.kvsdict)

    def tearDown(self):
        self.kvsdict.close()
        shutil.rmtree(DB_PATH)

    def test_init(self):
        self.assertTrue(os.path.exists(DB_PATH))

    def assertKeyValue(self, mapping):
        for k, v in mapping.items():
            self.assertTrue(self.kvsdict[k] == v)
        self.assertTrue(sorted(list(self.kvsdict.items())) == sorted([(k,v) for k,v in mapping.items()]))
        self.assertTrue(sorted(list(self.kvsdict.keys())) == sorted([k for k in mapping.keys()]))
        self.assertTrue(sorted(list(self.kvsdict.values())) == sorted([v for v in mapping.values()]))
        self.assertTrue(len(self.kvsdict) == len(mapping))

    def assertPrefixKeyValue(self, mapping):
        for k, v in mapping.items():
            self.assertTrue(self.pfdict[k] == v)
            self.assertTrue(self.kvsdict[self.pfdict.prefix.decode("utf8")+k] == v)
        self.assertTrue(sorted(list(self.pfdict.items())) == sorted([(k,v) for k,v in mapping.items()]))
        self.assertTrue(sorted(list(self.pfdict.keys())) == sorted([k for k in mapping.keys()]))
        self.assertTrue(sorted(list(self.pfdict.values())) == sorted([v for v in mapping.values()]))
        self.assertTrue(sorted(list(self.kvsdict.items())) == sorted([(self.pfdict.prefix.decode("utf8")+k,v) for k,v in mapping.items()]))
        self.assertTrue(sorted(list(self.kvsdict.keys())) == sorted([self.pfdict.prefix.decode("utf8")+k for k in mapping.keys()]))
        self.assertTrue(sorted(list(self.kvsdict.values())) == sorted([v for v in mapping.values()]))
        self.assertTrue(len(self.pfdict) == len(mapping))

    def test_dict(self):
        self.kvsdict["hoge"] = "hogehoge"
        self.assertKeyValue({
            "hoge": "hogehoge"
            })
        self.kvsdict["fuga"] = "fugafuga"
        self.assertKeyValue({
            "hoge": "hogehoge",
            "fuga": "fugafuga"
            })
        del self.kvsdict["fuga"]
        self.assertKeyValue({
            "hoge": "hogehoge"
            })

    def test_prefix_dict(self):
        self.pfdict["hoge"] = "hogehoge"
        self.assertPrefixKeyValue({
            "hoge": "hogehoge"
            })
        self.pfdict["fuga"] = "fugafuga"
        self.assertPrefixKeyValue({
            "hoge": "hogehoge",
            "fuga": "fugafuga"
            })
        del self.pfdict["fuga"]
        self.assertPrefixKeyValue({
            "hoge": "hogehoge"
            })

    def test_batch(self):
        d = {str(i):"hoge"+str(i) for i in range(100)}
        with self.kvsdict.write_batch() as wb:
            for k, v in d.items():
                wb[k] = v
        self.assertKeyValue(d)

        with self.kvsdict.write_batch() as wb:
            for k, v in d.items():
                del wb[k]
        self.assertKeyValue({})

        with self.kvsdict.write_batch(transaction=True) as wb:
            for k, v in d.items():
                wb[k] = v
        self.assertKeyValue(d)

        with self.kvsdict.write_batch(transaction=True) as wb:
            for k, v in d.items():
                del wb[k]
        self.assertKeyValue({})

        self.kvsdict.write_batch_mapping(d)
        self.assertKeyValue(d)

    def test_prefix_batch(self):
        d = {str(i):"hoge"+str(i) for i in range(100)}
        with self.pfdict.write_batch() as wb:
            for k, v in d.items():
                wb[k] = v
        self.assertPrefixKeyValue(d)

        with self.pfdict.write_batch() as wb:
            for k, v in d.items():
                del wb[k]
        self.assertPrefixKeyValue({})

        with self.pfdict.write_batch(transaction=True) as wb:
            for k, v in d.items():
                wb[k] = v
        self.assertPrefixKeyValue(d)

        with self.pfdict.write_batch(transaction=True) as wb:
            for k, v in d.items():
                del wb[k]
        self.assertPrefixKeyValue({})

        self.pfdict.write_batch_mapping(d)
        self.assertPrefixKeyValue(d)

    def test_alot(self):
        SIZE = 100000
        d = {str(i):"hoge"+str(i) for i in range(SIZE)}
        t = time.time()
        for k, v in d.items():
            self.kvsdict[k] = v
        print("{size} data has registerd in {sec} sec without batch".format(size=SIZE, sec=time.time()-t))

        t = time.time()
        with self.kvsdict.write_batch(transaction=True) as wb:
            for k, v in d.items():
                del wb[k]
        self.assertKeyValue({})
        print("{size} data has registerd in {sec} sec with batch".format(size=SIZE, sec=time.time()-t))


if __name__ == "__main__":
    unittest.main()
