import sys, os
sys.path.append(
    os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
    )
from jstatutree import get_etypes, LawData, ReikiData, ElementNumber
import unittest
from decimal import Decimal

class GetClassesTestCase(unittest.TestCase):
    def test_get_classes(self):
        import dummy_etypes as test_module
        classes = get_etypes(test_module)
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


if __name__ == "__main__":
    unittest.main()
