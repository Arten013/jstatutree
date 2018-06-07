import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
from jstatute_dict import JStatuteDict
import unittest
import xml_jstatutree as jstatutree

class LawDataTestCase(unittest.TestCase):
    def setUp(self):
        self.rr = jstatutree.ReikiXMLReader(
            os.path.join(
                os.path.dirname(__file__), "testset", "01/010001/0001.xml"
                )
            )
        self.rr.open()

    def setgetitem_testunit(self, assert_if, lawnum, only_reiki):
        jsdict = JStatuteDict(only_reiki=only_reiki)
        self.rr.lawdata._lawnum = lawnum
        if assert_if == "skip":
            jsdict[self.rr.lawdata] = self.rr
            self.assertTrue(len(jsdict) == 0)
        elif assert_if == "success":
            jsdict[self.rr.lawdata] = self.rr
            self.assertTrue(len(jsdict) == 1)
            self.assertTrue(jsdict[self.rr.lawdata] == self.rr)
        self.rr._lawdata = self.rr.get_lawdata()

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

if __name__ == "__main__":
    unittest.main()
