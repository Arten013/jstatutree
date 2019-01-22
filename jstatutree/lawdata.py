from decimal import Decimal
import re
from .exceptions import LawElementNumberError
import unicodedata
import os

class LawData(object):
    def __init__(self, code=None, path=None):
        self._name = None
        self._lawnum = None
        if path is not None:
            self.code = ReikiCode.init_from_path(path)
        else:
            self.code = code or ReikiCode()

    @property
    def title(self):
        return "UNK" if self._name is None else self._name

    @title.setter
    def title(self, title):
        self._name = title

    @property
    def name(self):
        from .etypes import code2jname
        return ("UNK" if self._name is None else self._name)+code2jname(str(self.code))

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
        return True if re.search("[日市区町村](?:条例|規則)", self.lawnum) else False

    @property
    def prefecture_code(self):
        assert isinstance(self.code, ReikiCode), 'Non-reiki data has no reiki code'
        return self.code.prefecture_code

    @prefecture_code.setter
    def prefecture_code(self, val):
        self.code.prefecture_code = val

    @property
    def municipality_code(self):
        assert isinstance(self.code, ReikiCode), 'Non-reiki data has no reiki code'
        return self.code.municipality_code

    @municipality_code.setter
    def municipality_code(self, val):
        self.code.municipality_code = val

    @property
    def file_code(self):
        return self.code.file_code

    @file_code.setter
    def file_code(self, val):
        self.code.file_code = val

    @property
    def id(self):
        return int(self.code)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.code == other.code

    def __hash__(self):
        return hash(self.code)

from pathlib import Path
class ReikiCode(object):
    def __init__(self, codestr=None):
        if isinstance(codestr, ReikiCode):
            self.prefecture_code, self.municipality_code, self.file_code = codestr.prefecture_code, codestr.municipality_code, codestr.file_code
        elif codestr:
            self.prefecture_code, self.municipality_code, self.file_code = Path(codestr).parts[:3]
        else:
            self._prefecture_code, self._municipality_code, self._file_code = None, None, None

    _path_code_extract_ptn = re.compile('/(\d{2}/\d{6}/\d{4})(\.xml)?$')
    @classmethod
    def init_from_path(cls, path):
        path = str(path)
        return cls(re.search(cls._path_code_extract_ptn, path).group(1))
    
    @property
    def prefecture_code(self):
        return self._prefecture_code or '00'

    @prefecture_code.setter
    def prefecture_code(self, val):
        assert isinstance(val, (str, int)), "invalid prefecture_code" + str(val)
        if isinstance(val, str):
            assert re.match('\d+', val), "invalid prefecture_code" + str(val)
        assert 0 < int(val) <= 47, "invalid prefecture_code" + str(val)
        self._prefecture_code = "{0:02}".format(int(val))

    @property
    def municipality_code(self):
        return self._municipality_code or '000000'

    @municipality_code.setter
    def municipality_code(self, val):
        assert isinstance(val, (str, int)), "invalid municipality_code" + str(val)
        if isinstance(val, str):
            assert re.match('\d+', val), "invalid municipality_code" + str(val)
        assert 10000 <= int(val) < 480000, "invalid municipality_code" + str(val)
        self._municipality_code = "{0:06}".format(int(val))

    @property
    def file_code(self):
        return self._file_code or '0000'

    @file_code.setter
    def file_code(self, val):
        assert isinstance(val, (str, int)), "invalid file_code" + str(val)
        if isinstance(val, str):
            assert re.match('\d+', val), "invalid file_code" + str(val)
        assert 0 <= int(val) < 10000, "invalid file_code" + str(val)
        self._file_code = "{0:04}".format(int(val))

    def __int__(self):
        return int(self.municipality_code) * 10000 + int(self.file_code)

    def __str__(self):
        return os.path.join(*list(self))

    def __iter__(self):
        yield from (self.prefecture_code, self.municipality_code, self.file_code)

    def to_path(self, prefix=''):
        f = str(self)+'.xml'
        return Path(prefix) / Path(f)

    def __hash__(self):
        return hash(str(self))

    def __contains__(self, item):
        str(self) in item

# 例規のメタデータ
ReikiData = LawData

class ElementNumber(object):
    def __init__(self, value):
        if isinstance(value, str):
            self.num = self.str_to_decimal(value)
        elif isinstance(value, ElementNumber):
            self.num = ElementNumber.num
        else:
            self.num = Decimal(value)

    def __int__(self):
        return int(self.num)
            
    @property
    def main_num(self):
        return self.num.quantize(Decimal('1'))

    @property
    def branch_nums(self):
        branch_nums = []
        num = self.num
        while num.quantize(Decimal('1')) != Decimal(0):
            branch_nums += [num.quantize(Decimal('1'))]
            num = num - num.quantize(Decimal('1'))
            num *= 1000
        return branch_nums[1:]

    _str_matching_ptn = re.compile("^[0-9]+(?:_[0-9]+)+$")
    @classmethod
    def str_to_decimal(cls, strnum):
        if strnum == "":
            return Decimal(1)
        if re.match('\d+$', strnum):
            return Decimal(strnum)
        m = re.match(cls._str_matching_ptn, strnum)
        if m:
            num = Decimal(0)
            mul = Decimal(1)
            for n in strnum.split("_"):
                num += Decimal(n) * mul
                mul /= Decimal(1000)
            return num
        if re.match('\d+:\d', strnum):
            return Decimal(re.split(':', strnum)[0])
        raise LawElementNumberError(error_detail="Invalid Format {}".format(strnum))

    def __lt__(self, other):
        if isinstance(other, ElementNumber):
            return self.num.__lt__(other.num)
        return self.num.__lt__(Decimal(other))

    def __eq__(self, other):
        if isinstance(other, ElementNumber):
            return self.num.__eq__(other.num)
        return self.num.__eq__(Decimal(other))

    def __hash__(self):
        return hash(self.num)

