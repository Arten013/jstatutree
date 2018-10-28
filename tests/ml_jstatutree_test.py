import unittest
import sys, os
from jstatutree.xmltree import xml_lawdata
from jstatutree.xmltree import xml_etypes
from jstatutree.mltree import ml_lawdata
from jstatutree.mltree import ml_etypes
from jstatutree.lawdata import LawData
import shutil

TEST_PATH = os.path.dirname(__file__)
DB_PATH = os.path.join(TEST_PATH, "testdb")
class ReikiKVSReaderTestCase(unittest.TestCase):
    def setUp(self):
        testset_path = os.path.join(os.path.dirname(__file__), "testset/01/010001/0001.xml")
        self.xml_rr = xml_lawdata.ReikiXMLReader(testset_path)
        self.xml_rr.open()
        assert self.xml_rr.get_tree() is not None, "test set path is invalid.\n"+str(testset_path)

        writer = ml_lawdata.JStatutreeKVS(DB_PATH)
        writer.set_from_reader(self.xml_rr)
        #print("writer: ",list(writer["lawdata"].items()))
        self.rr = ml_lawdata.ReikiKVSReader(code="01/010001/0001", db=writer)
        #print("reader: ",list(self.rr.db["lawdata"].items()))

    def test_get_lawdata(self):
        ld = self.rr.lawdata
        self.assertTrue(issubclass(ld.__class__, LawData))
        self.assertEqual(ld.code, "01/010001/0001")
        self.assertEqual(ld.name, "法令名")
        self.assertEqual(ld.lawnum, "法令番号")

    def element_match(self, elem, etype, num, text):
        self.assertEqual(etype, elem.etype)
        self.assertEqual(num, int(elem.num.num))
        self.assertEqual(text, elem.text)

    def test_get_tree(self):
        tree = self.rr.get_tree()
        self.assertTrue(isinstance(tree, ml_etypes.Law))
        answers = [
            [ml_etypes.Law, 1, ""],
            [ml_etypes.LawBody, 1, ""],
            [ml_etypes.MainProvision, 1, ""],
            [ml_etypes.Article, 1, ""],
            [ml_etypes.ArticleCaption, 1, "(第一条 条見出し)"],
            [ml_etypes.Paragraph, 1, ""],
            [ml_etypes.ParagraphSentence, 1, ""],
            [ml_etypes.Sentence, 1, "第一項本文"],
            [ml_etypes.Article, 2, ""],
            [ml_etypes.ArticleCaption, 1, "(第二条 条見出し)"],
            [ml_etypes.Paragraph, 1, ""],
            [ml_etypes.ParagraphSentence, 1, ""],
            [ml_etypes.Sentence, 1, "第一項本文"],
            [ml_etypes.Paragraph, 2, ""],
            [ml_etypes.ParagraphSentence, 1, ""],
            [ml_etypes.Sentence, 1, "第二項本文"],
            [ml_etypes.Sentence, 2, "第二項但し書き"],
            [ml_etypes.Paragraph, 3, ""],
            [ml_etypes.ParagraphSentence, 1, ""],
            [ml_etypes.Sentence, 1, "第三項柱書き"],
            [ml_etypes.Item, 1, ""],
            [ml_etypes.ItemSentence, 1, ""],
            [ml_etypes.Sentence, 1, "第一号第一文"],
            [ml_etypes.Sentence, 2, "第一号第二文"],
            [ml_etypes.Item, 2, ""],
            [ml_etypes.ItemSentence, 1, ""],
            [ml_etypes.Sentence, 1, "第二号柱書き"],
            [ml_etypes.Subitem1, 1, ""],
            [ml_etypes.Subitem1Sentence, 1, ""],
            [ml_etypes.Sentence, 1, "第一号柱書き"],
            [ml_etypes.Subitem2, 1, ""],
            [ml_etypes.Subitem2Sentence, 1, ""],
            [ml_etypes.Sentence, 1, "第一号柱書き"],
            [ml_etypes.Item, 3, ""],
            [ml_etypes.ItemSentence, 1, ""],
            [ml_etypes.Column, 1, ""],
            [ml_etypes.Sentence, 1, "第三号第一文"],
            [ml_etypes.Sentence, 2, "第三号第二文"],

        ]
        for i, child in enumerate(tree.depth_first_iteration()):
            #print(child.etype.__name__)
            #print((child, int(child.num.num), child.text), answers[i])
            self.element_match(child, *answers[i])

    def tearDown(self):
        self.xml_rr.close()
        self.rr.close()
        shutil.rmtree(DB_PATH)

    def velement_match(self, elem, etype, num=0, text="", is_vnode=True):
        print(elem, "{}(vnode)".format(elem.etype.__name__) if elem.is_vnode else "{}".format(elem.etype.__name__))
        self.assertEqual(etype, elem.etype)
        self.assertEqual(num, int(elem.num.num))
        self.assertEqual(text, elem.text)
        self.assertEqual(elem.is_vnode, is_vnode)

    def elements_match(self, tree, target_type, patterns=[[]]):
        from pprint import pprint
        for i, e in enumerate(tree.depth_first_search(target_type, valid_vnode=True)):
            self.velement_match(e, target_type, *patterns[i])

    def test_depth_first_search(self):
        tree = self.rr.get_tree()
        self.elements_match(tree, ml_etypes.Law, patterns=[[1, "", False]])
        self.elements_match(tree, ml_etypes.LawBody, patterns=[[1, "", False]])
        self.elements_match(tree, ml_etypes.MainProvision, patterns=[[1, "", False]])
        self.elements_match(tree, ml_etypes.Part)
        self.elements_match(tree, ml_etypes.Chapter)
        self.elements_match(tree, ml_etypes.Section)
        self.elements_match(tree, ml_etypes.Subsection)
        self.elements_match(tree, ml_etypes.Division)
        self.elements_match(tree, ml_etypes.Item, patterns=
            [
                [0, "", True],
                [0, "", True],
                [0, "", True],
                [1, "", False ],
                [2, "", False ],
                [3, "", False ]
            ]
            )
        self.elements_match(tree, ml_etypes.Column, patterns=
           [[0, "", True]] * 8 + [[1, "", False]]
            )
        self.elements_match(tree, ml_etypes.Subitem1, patterns=
            [
                [0, "", True],
                [0, "", True],
                [0, "", True],
                [0, "", True ],
                [0, "", True ],
                [1, "", False ],
                [0, "", True ],
            ]
            )

if __name__ == "__main__":
    unittest.main()
