from abc import abstractmethod
import inspect
from decimal import Decimal
import re
from .myexceptions import LawElementNumberError, HieralchyError
import unicodedata

class SourceInterface(object):
    @property
    def lawdata(self):
        if "_lawdata" not in self.__dict__ or self._lawdata is None:
            if self.is_closed():
                self.open()
                self._lawdata = self.read_lawdata()
                self.close()
            else:
                self._lawdata = self.read_lawdata()
        return self._lawdata     

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_tree(self):
        pass

    @abstractmethod
    def read_lawdata(self):
        pass

    def __eq__(self, other):
        if not issubclass(other.__class__, SourceInterface):
            return False
        return self.lawdata == other.lawdata

    def __hash__(self):
        return hash(self.lawdata)

class LawData(object):
    def __init__(self):
        self._name = None
        self._lawnum = None
        self._code = None

    @property
    def name(self):
        return "UNK" if self._name is None else self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def lawnum(self):
        return "UNK" if self._lawnum is None else self._lawnum

    @lawnum.setter
    def lawnum(self, lawnum):
        self._lawnum = lawnum

    def is_reiki(self):
        return True if re.search("(?:条例|規則)", self.lawnum) else False

    @property
    def code(self):
        return self.lawnum

# 例規のメタデータ
class ReikiData(LawData):
    def __init__(self):
        super().__init__()
        self._code = "00/000000/0000"
        self._id = 0
        self._prefecture_code = "00"
        self._municipality_code = "000000"
        self._file_code = "0000"

    @property
    def prefecture_code(self):
        return self._prefecture_code

    @prefecture_code.setter
    def prefecture_code(self, val):
        assert isinstance(val, (str, int)), "invalid prefecture_code" + str(val)
        assert 0 < int(val) <= 47, "invalid prefecture_code" + str(val)
        self._prefecture_code = "{0:02}".format(int(val))

    @property
    def municipality_code(self):
        return self._municipality_code

    @municipality_code.setter
    def municipality_code(self, val):
        assert isinstance(val, (str, int)), "invalid municipality_code" + str(val)
        assert 10000 <= int(val) < 480000, "invalid municipality_code" + str(val)
        self._municipality_code = "{0:06}".format(int(val))

    @property
    def file_code(self):
        return self._file_code

    @file_code.setter
    def file_code(self, val):
        assert isinstance(val, (str, int)), "invalid file_code" + str(val)
        assert 0 <= int(val) < 10000, "invalid file_code" + str(val)
        self._file_code = "{0:04}".format(int(val))


    @property
    def code(self):
        if self._code == "00/000000/0000":
            self._code = "/".join(
                [self.prefecture_code, 
                self.municipality_code, 
                self.file_code]
                )
        return self._code

    @property
    def id(self):
        if self._id is 0:
            self._id = int(self.municipality_code) * 10000 + int(self.file_code)
        return self._id

    def __eq__(self, other):
        if not issubclass(other.__class__, ReikiData):
            return False
        return self.code == other.code

    def __hash__(self):
        return hash(self.code)


class ElementNumber(object):
    def __init__(self, arg):
        if isinstance(arg, int):
            self.num = Decimal(arg)     
        elif isinstance(arg, str):
            self.num = self.str_to_decimal(arg)
        elif isinstance(arg, (Decimal,)):
            self.num = arg
        elif isinstance(arg, (ElementNumber,)):
            self.num = arg.num
        else:
            raise TypeError("Invalid type for init ElementNumber: {}".format(arg.__class__.__name__))

    def __float__(self):
        return float(self.num)

    @property
    def main_num(self):
        return self.num.quantize(Decimal('1'))

    @property
    def branch_nums(self):
        branch_nums = []
        num = self.num - self.main_num
        while num.quantize(Decimal('1')) != Decimal(0):
            num *= 100
            branch_nums += [num.quantize(Decimal('1'))]
            num = num - num.quantize(Decimal('1'))
        return branch_nums

    def str_to_decimal(self, strnum):
        if strnum == "":
            return Decimal(1)
        if re.match("^[0-9]+(?:_[0-9]+)*$", strnum) is None:
            raise LawElementNumberError(error_detail="Invalid Format {}".format(strnum))
        num = Decimal(0)
        mul = Decimal(1)
        for n in strnum.split("_"):
            num += Decimal(n) * mul
            mul /= Decimal(1000)
        return num
