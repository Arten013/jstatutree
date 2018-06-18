import sys, os
from jstatutree.jstatute_dict import JStatuteDict, JStatutreeKVSDict, JSSentenceKVSDict
import unittest
from jstatutree import lawdata
from jstatutree.xmltree import xml_lawdata as xml_lawdata
from jstatutree.etypes import Law, Article, Sentence
import shutil

class LawDataTestCase(unittest.TestCase):
    def setgetitem_testunit(self, assert_if, lawnum, only_reiki):
        jsdict = JStatuteDict(only_reiki=only_reiki)
        statute = lawdata.SourceInterface()
        statute._lawdata = lawdata.LawData()
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

TEST_PATH = os.path.dirname(__file__)
DB_PATH = os.path.join(TEST_PATH, "testdb.ldb")
DATASET_PATH = os.path.join(TEST_PATH, "testset")
class JSKVSTestCase(unittest.TestCase):
    def setUp(self):
        self.levels = [Law, Article, Sentence]
        self.treedict = JStatutreeKVSDict(path=DB_PATH, levels=self.levels, create_if_missing=True)
        self.sentence_dicts = {
                level.__name__: JSSentenceKVSDict(kvsdict=self.treedict, level=level)
                for level in self.levels
            }
        self.rr = xml_lawdata.ReikiXMLReader(
            os.path.join(
                os.path.dirname(__file__), "testset/01/010001/0001.xml"
                )
            )
        self.rr.open()

    def tearDown(self):
        self.treedict.close()
        shutil.rmtree(DB_PATH)

    def test_init(self):
        self.assertTrue(self.treedict.levels == [Law, Article, Sentence])
        for level in self.levels:
            self.assertTrue(self.sentence_dicts[level.__name__].prefix == "sentence-{}-".format(level.__name__).encode(self.sentence_dicts[level.__name__].ENCODING))


    def regtree_test_unit(self, elem, next_level_i):
        print(elem.etype.__name__, self.levels[next_level_i].__name__)
        correct_next_elems = list(elem.depth_first_search(self.levels[next_level_i]))
        correct_next_elem_codes = sorted([e.code for e in correct_next_elems])
        self.assertEqual(sorted(self.treedict[elem.code]), correct_next_elem_codes)
        for next_elem in elem.depth_first_search(self.levels[next_level_i]):
            if next_level_i+1 < len(self.levels):
                self.regtree_test_unit(next_elem, next_level_i+1)

    def test_regtree(self):
        ld = self.rr.lawdata
        ld.is_reiki = lambda:  True
        tree = self.rr.get_tree()
        self.treedict[self.rr.lawdata.code] = tree


if __name__ == "__main__":
    unittest.main()
