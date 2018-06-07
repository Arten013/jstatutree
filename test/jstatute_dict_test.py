import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
from jstatute_dict import JStatuteDict
import unittest
import jstatutree

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

if __name__ == "__main__":
    unittest.main()
