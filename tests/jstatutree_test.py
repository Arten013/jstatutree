import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
from jstatutree.lawdata import LawData, ReikiData, ElementNumber
from jstatutree.etypes import get_etypes
from jstatutree.xmltree import xml_etypes, xml_lawdata
import unittest
from decimal import Decimal

class GetClassesTestCase(unittest.TestCase):
    def test_get_classes(self):
        from . import dummy_etypes as test_module
        classes = test_module.get_etypes()
        self.assertEqual(classes[0], test_module.Law)
        classes = sorted(classes, key=lambda x: x.__name__)
        self.assertEqual(
            classes,
            [
                test_module.Law,
                test_module.LawBody,
                test_module.MainProvision,
                test_module.Part
            ]
            )

class LawDataTestCase(unittest.TestCase):
    def setUp(self):
        self.ld = LawData()
        self.rd = ReikiData()

    def test_lawdata(self):
        self.lawdata_test_base(self.ld)

    def lawdata_test_base(self, ld):
        self.assertEqual(ld.name, "UNK")
        self.assertEqual(ld.lawnum, "UNK")
        self.assertEqual(ld._name, None)
        self.assertEqual(ld._lawnum, None)
        ld.name = "hoge"
        ld.lawnum = "fuga"
        self.assertEqual(ld.name, "hoge")
        self.assertEqual(ld.lawnum, "fuga")

    def test_reikidata_init(self):
        self.lawdata_test_base(self.rd)
        self.assertEqual(self.rd.id, 0)
        self.assertEqual(self.rd.code, "00/000000/0000")

    def test_reikidata_strcode(self):
        self.rd.prefecture_code = "01"
        self.rd.municipality_code = "010001"
        self.rd.file_code = "0001"
        self.assertEqual(self.rd.id, 100010001)
        self.assertEqual(self.rd.code, "01/010001/0001")

    def test_reikidata_intcode(self):
        self.rd.prefecture_code = 1
        self.rd.municipality_code = 10001
        self.rd.file_code = 1
        self.assertEqual(self.rd.id, 100010001)
        self.assertEqual(self.rd.code, "01/010001/0001")

    def reikidata_insert_attr_raises(self, val, attr):
        self.assertRaises(
            Exception,
            lambda: setattr(self.ld, attr, val)
            )

    def test_reikidata_failurecode(self):
        self.reikidata_insert_attr_raises("prefecture_code", 100)
        self.reikidata_insert_attr_raises("prefecture_code", -1)
        self.reikidata_insert_attr_raises("prefecture_code", 1.1)

        self.reikidata_insert_attr_raises("municipality_code", 10000000)
        self.reikidata_insert_attr_raises("municipality_code", -1)
        self.reikidata_insert_attr_raises("municipality_code", 1.1)

        self.reikidata_insert_attr_raises("file_code", 10000)
        self.reikidata_insert_attr_raises("file_code", -1)
        self.reikidata_insert_attr_raises("file_code", 1.1)

class ElementNumberTestCase(unittest.TestCase):
    def check_valid_values(self, v, *correct_nums):
        n = ElementNumber(v)
        self.assertEqual(n.main_num, correct_nums[0])
        for bn in enumerate(n.branch_nums):
            self.assertTrue(isinstance(bn, correct_nums[1+i]))

    def test_init(self):
        self.check_valid_values(0, 0)
        self.check_valid_values(100, 100)
        self.check_valid_values(Decimal(100), 100)
        self.check_valid_values(ElementNumber(100), 100)
        self.check_valid_values("0", 0)
        self.check_valid_values("100", 100)
        self.check_valid_values("1_1", 1, 1)
        self.check_valid_values("1_1_1", 1, 1, 1)
from jstatutree.xmltree import xml_lawdata
from jstatutree.xmltree import xml_etypes

class VirtualEtypesTestCase(unittest.TestCase):
    def setUp(self):
        testset_path = os.path.join(os.path.dirname(__file__), "testset/01/010001/0001.xml")
        self.rr = xml_lawdata.ReikiXMLReader(testset_path)
        self.rr.open()
        assert self.rr.get_tree() is not None, "test set path is invalid.\n"+str(testset_path)

    def test_get_lawdata(self):
        ld = self.rr.lawdata
        self.assertTrue(issubclass(ld.__class__, xml_lawdata.LawData))
        self.assertEqual(ld.code, "01/010001/0001")
        self.assertEqual(ld.name, "法令名")
        self.assertEqual(ld.lawnum, "法令番号")

    def element_match(self, elem, etype, num=0, text="", is_vnode=True):
        print(elem, "{}(vnode)".format(elem.etype.__name__) if elem.is_vnode else "{}".format(elem.etype.__name__))
        self.assertEqual(etype, elem.etype)
        self.assertEqual(num, int(elem.num.num))
        self.assertEqual(text, elem.text)
        self.assertEqual(elem.is_vnode, is_vnode)

    def elements_match(self, tree, target_type, patterns=[[]]):
        for i, e in enumerate(tree.depth_first_search(target_type, valid_vnode=True)):
            self.element_match(e, target_type, *patterns[i])

    def test_depth_first_search(self):
        tree = self.rr.get_tree()
        self.elements_match(tree, xml_etypes.Law, patterns=[[1, "", False]])
        self.elements_match(tree, xml_etypes.LawBody, patterns=[[1, "", False]])
        self.elements_match(tree, xml_etypes.MainProvision, patterns=[[1, "", False]])
        self.elements_match(tree, xml_etypes.Part)
        self.elements_match(tree, xml_etypes.Chapter)
        self.elements_match(tree, xml_etypes.Section)
        self.elements_match(tree, xml_etypes.Subsection)
        self.elements_match(tree, xml_etypes.Division)
        self.elements_match(tree, xml_etypes.Item, patterns=
            [
                [0, "", True],
                [0, "", True],
                [0, "", True],
                [1, "", False ],
                [2, "", False ]
            ]
            )
        self.elements_match(tree, xml_etypes.Subitem1, patterns=
            [
                [0, "", True],
                [0, "", True],
                [0, "", True],
                [0, "", True ],
                [0, "", True ],
                [1, "", False ]
            ]
            )





if __name__ == "__main__":
    unittest.main()
