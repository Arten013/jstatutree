import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
from jstatutree.jstatute_dict import JStatuteDict, JStatutreeKVSDict, JSSentenceKVSDict
import unittest
import jstatutree.jstatutree
from jstatutree.etypes import Law, Article, Sentence

class LawDataTestCase(unittest.TestCase):
    def setgetitem_testunit(self, assert_if, lawnum, only_reiki):
        jsdict = JStatuteDict(only_reiki=only_reiki)
        statute = jstatutree.SourceInterface()
        statute._lawdata = jstatutree.LawData()
        statute.lawdata._lawnum = lawnum
        if assert_if == "skip":
            jsdict[statute.lawdata] = statute
            self.assertTrue(len(jsdict) == 0)
        elif assert_if == "success":
            jsdict[statute.lawdata] = statute
            self.assertTrue(len(jsdict) == 1)
            self.assertTrue(jsdict[statute.lawdata] == statute)

    def test_setgetitem(self):
        self.setgetitem_testunit("success", "XX条例", True)
        self.setgetitem_testunit("success", "XX規則", True)
        self.setgetitem_testunit("skip", "XX告示", True)
        self.setgetitem_testunit("success", "XX条例", False)
        self.setgetitem_testunit("success", "XX規則", False)
        self.setgetitem_testunit("success", "XX告示", False)
        self.assertRaises(
            Exception,
            lambda: JStatuteDict().__setitem__("hoge", "fuga")
            )

import shutil
TEST_PATH = os.path.dirname(__file__)
DB_PATH = os.path.join(TEST_PATH, "testdb.ldb")
DATASET_PATH = os.path.join(TEST_PATH, "testset")
class JSKVSTestCase(unittest.TestCase):
    def setUp(self):
        self.levels = [Law, Sentence, Article]
        self.treedict = JStatutreeKVSDict(path=DB_PATH, levels=self.levels, create_if_missing=True)
        self.sentence_dicts = {
                level.__name__: JSSentenceKVSDict(db=self.treedict, level=level)
                for level in self.levels
            }

    def tearDown(self):
        self.treedict.close()
        shutil.rmtree(DB_PATH)

    def test_init(self):
        self.assertTrue(self.treedict.levels == [Law, Article, Sentence])
        for level in self.levels:
            self.assertTrue(self.sentence_dicts[level.__name__].prefix == "sentence-{}-".format(level.__name__).encode(self.sentence_dicts[level.__name__].ENCODING))

if __name__ == "__main__":
    unittest.main()
