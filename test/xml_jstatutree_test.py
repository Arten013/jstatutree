import unittest
import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
import xml_jstatutree as jstatutree
import xml_etypes as etype

class ReikiXMLReaderTestCase(unittest.TestCase):
    def setUp(self):
        self.rr = jstatutree.ReikiXMLReader(
        	os.path.join(
        		os.path.dirname(__file__), "testset", "01/010001/0001.xml"
        		)
        	)
        self.rr.open()

    def test_get_lawdata(self):
    	ld = self.rr.lawdata
    	self.assertTrue(issubclass(ld.__class__, jstatutree.LawData))
    	self.assertEqual(ld.code, "01/010001/0001")
    	self.assertEqual(ld.name, "法令名")
    	self.assertEqual(ld.lawnum, "法令番号")

    def element_match(self, elem, etype, num, text):
        self.assertEqual(etype, elem.etype)
        self.assertEqual(num, int(elem.num.num))
        self.assertEqual(text, elem.text)

    def test_get_tree(self):
        tree = self.rr.get_tree()
        self.assertTrue(isinstance(tree, etype.Law))
        answers = [
            [etype.Law, 1, ""],
            [etype.LawBody, 1, ""],
            [etype.MainProvision, 1, ""],
            [etype.Article, 1, ""],
            [etype.ArticleCaption, 1, "(第一条 条見出し)"],
            [etype.Paragraph, 1, ""],
            [etype.ParagraphSentence, 1, ""],
            [etype.Sentence, 1, "第一項本文"],
            [etype.Article, 2, ""],
            [etype.ArticleCaption, 1, "(第二条 条見出し)"],
            [etype.Paragraph, 1, ""],
            [etype.ParagraphSentence, 1, ""],
            [etype.Sentence, 1, "第一項本文"],
            [etype.Paragraph, 2, ""],
            [etype.ParagraphSentence, 1, ""],
            [etype.Sentence, 1, "第二項本文"],
            [etype.Sentence, 2, "第二項但し書き"],
            [etype.Paragraph, 3, ""],
            [etype.ParagraphSentence, 1, ""],
            [etype.Sentence, 1, "第三項柱書き"],
            [etype.Item, 1, ""],
            [etype.ItemSentence, 1, ""],
            [etype.Sentence, 1, "第一号第一文"],
            [etype.Sentence, 2, "第一号第二文"],
            [etype.Item, 2, ""],
            [etype.ItemSentence, 1, ""],
            [etype.Sentence, 1, "第二号柱書き"],
            [etype.Subitem1, 1, ""],
            [etype.Subitem1Sentence, 1, ""],
            [etype.Sentence, 1, "第一号柱書き"],
            [etype.Subitem2, 1, ""],
            [etype.Subitem2Sentence, 1, ""],
            [etype.Sentence, 1, "第一号柱書き"],

        ]
        for i, child in enumerate(tree.depth_first_iteration()):
            print(child, answers[i])
            self.element_match(child, *answers[i])

    def tearDown(self):
        self.rr.close()


if __name__ == "__main__":
    unittest.main()