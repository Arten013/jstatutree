from abc import abstractmethod
import inspect
from decimal import Decimal
import re

class SourceInterface(object):
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
    def get_lawdata(self):
        pass

def get_classes(module):
    return set(map(lambda x:x[1],inspect.getmembers(module,inspect.isclass)))

# 法令文書を扱うためのTree
class JpnStatuTree(object):
    def __init__(self, source):
        self.source = source
        self.source.open()
        self.lawdata = self.source.get_lawdata()
        self.source.close()

    def get_tree(self):
        return self.source.get_tree()

    def __str__(self):
        return "{name} ({num})".format(name=self.lawdata.name, num=self.lawdata.num)

    def is_reiki(self):
        return True if re.search("(?:条例|規則)", self.lawdata.lawnum) else False

class LawData(object):
    def __init__(self):
        self._name = None
        self._lawnum = None

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

# 要素の基底クラス
class TreeElement(object):
    PARENT_CANDIDATES = ()
    CHILDREN_PATTERNS = ()
    JNAME = ""

    def __init__(self, parent=None):
        self.parent = parent
        self._lawdata = None
        self._num
        self._children = None
        self._text = None

    # 親から子を生成する場合は__init__を直接呼ばずにこちらで初期化する
    @classmethod
    def inheritance(cls, parent):
        if not isinstance(parent, cls.PARENT_CANDIDATES):
            raise HieralchyError(
                parent.lawdata,
                "invalid hieralchy "+parent.etype + " -> " + cls.__name__
            )
        child = cls(parent)
        return child

    # "X法第n条第m項"のように出力
    def __str__(self):
        return str(self.parent)+str(self.num)

    # 呼び出し時に読み出す(children, name, text)
    @property
    def children(self):
        if self._children is None:
            self._children = self._find_children()
        return self._children

    @property
    def num(self):
        if self._num is None:
            self._num = self._read_num()
        return self._num

    # 条見出しやsentence等文字列はすべてtextとして扱う
    @property
    def text(self):
        if self._text is None:
            self._text = self.preprocess_str(self._read_text())
        return self._text

    # "第n条", "条見出し"のような要素名
    @property
    def name(self):
        if "branch" in self.JNAME:
            return JNAME.format(
                num=int(self.num.main_num),
                branch="の".join(map(lambda x: int(x), self.num.branch_nums))
            )
        elif "num" in self.JNAME:
            return JNAME.format(
                num=int(self.num.main_num)
            )
        else:
            return self.JNAME

    @property
    def lawdata(self):
        if self._lawdata is not None:
            return self.parent.lawdata
        return self._lawdata

    @lawdata.setter
    def lawdata(self, lawdata):
        assert issubclass(lawdata.__class__, LawData), "Lawdata must be supplied as a subclass of LawData."
        self._lawdata = lawdata 

    @property
    def etype(self):
        return self.__class__

    @classmethod
    def preprocess_str(self, str):
        return unicodedata.normalize("NFKC", s)

    def _read_num(self):
        return LawElementNumber(self.etype, "0")

    @abstractmethod
    def _read_children_list(self):
        pass

    @abstractmethod
    def _read_text(self):
        pass

    # 子要素を探索
    # 継承先でこのメソッドを書き換えるのは非推奨
    def _find_children(self):
        children= dict
        for child in self._read_children_list():
            # 要素の重複がないかチェック
            if children.name in children.keys():
                raise HieralchyError(
                    self.lawdata,
                    "element number duplication: {0}".format(str(child))
                )
            children[name] = child
        """
        # 兄弟関係が不正でないかチェック
        etypes = set(map(lambda x: x.etype, children))
        if etypes not in self.__class__.CHILDREN_PATTERNS:
            raise HieralchyError(
                self.lawdata, 
                "Invalid Brothers: {}".format(", ".join(etypes))
                )
            
        """
        return children

    def is_leaf(self):
        return len(self.children) == 0

    def has_text(self):
        return len(self.texts) == 0

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
        if re.match("^[0-9]+(?:_[0-9]+)*$", strnum) is None:
            raise LawElementNumberError(error_detail="Invalid Format {}".format(strnum))
        num = Decimal(0)
        mul = Decimal(1)
        for n in strnum.split("_"):
            num += Decimal(n) * mul
            mul /= Decimal(1000)
        return num
