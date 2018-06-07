from abc import abstractmethod
import inspect
from decimal import Decimal
import re
from myexceptions import LawElementNumberError, HieralchyError
import unicodedata

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

    def __eq__(self, other):
        if not issubclass(other.__class__, SourceInterface):
            return False
        return self.lawdata == other.lawdata

    def __hash__(self):
        return hash(self.lawdata)

def get_etypes(module):
    etypes = []
    root = None
    for i in inspect.getmembers(module, inspect.isclass):
        etype_name, etype_cls = i[:2]
        if not hasattr(etype_cls, "etype") or "Expansion" in etype_name:
            continue
        if etype_cls.is_root():
            assert root is None, "root elem has to be unique."
            root = etype_cls
        else:
            etypes.append(etype_cls)
    assert root is not None, "No root has been defined."+str(etypes)
    return [root] + etypes

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

    def is_reiki(self):
        return True if re.search("(?:条例|規則)", self.lawnum) else False


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

# 要素の基底クラス
class TreeElement(object):
    PARENT_CANDIDATES = ()
    CHILDREN_PATTERNS = ()
    JNAME = ""

    def __init__(self, parent=None):
        self.parent = parent
        self._num = None
        self._children = None
        self._text = None

    # 親から子を生成する場合は__init__を直接呼ばずにこちらで初期化する
    @classmethod
    def inheritance(cls, parent):
        if not isinstance(parent, cls.PARENT_CANDIDATES):
            raise HieralchyError(
                parent.lawdata,
                "invalid hieralchy "+parent.etype.__name__ + " -> " + cls.__name__
            )
        child = cls(parent)
        return child

    # "X法第n条第m項"のように出力
    def __str__(self):
        return str(self.parent)+str(self.name)

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
            return self.JNAME.format(
                num=int(self.num.main_num),
                branch="の".join(map(lambda x: int(x), self.num.branch_nums))
            )
        elif "num" in self.JNAME:
            return self.JNAME.format(
                num=int(self.num.main_num)
            )
        else:
            return self.JNAME

    @property
    def lawdata(self):
        return self.parent.lawdata

    @lawdata.setter
    def lawdata(self, lawdata):
        assert issubclass(lawdata.__class__, LawData), "Lawdata must be supplied as a subclass of LawData."
        self._lawdata = lawdata 

    @property
    def etype(self):
        return self.__class__

    @classmethod
    def preprocess_str(self, s):
        return unicodedata.normalize("NFKC", s).strip()

    def _read_num(self):
        return LawElementNumber("1")

    @abstractmethod
    def _read_children_list(self):
        pass

    @abstractmethod
    def _read_text(self):
        pass

    # 子要素を探索
    # 継承先でこのメソッドを書き換えるのは非推奨
    def _find_children(self):
        children = dict()
        for child in self._read_children_list():
            # 要素の重複がないかチェック
            #print(child, child.etype.__name__)
            if child in children.values():
                raise HieralchyError(
                    self.lawdata,
                    "element number duplication: {0} in {1}".format(str(child), str(list(map(lambda x: str(x), children.values()))))
                )
            children[child.name] = child
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

    @classmethod
    def is_root(cls):
        return False

    def depth_first_iteration(self, target=None):
        yield self
        if target != self.etype.__name__:
            for child in sorted(self.children.values()):
                yield from child.depth_first_iteration(target)

    def iter_sentences(self):
        for child in self.depth_first_iteration():
            if child.etype.__name__ == "Sentence":
                yield child.text

    def _comparable_check(self, elem):
        #assert elem.__class__ in ((self.etype,) + self.BROTHER_CANDIDATES), "cannot compare {} and {}".format(self.etype, elem.__class__)
        assert hasattr(self, "num"), "cannot compare elements without element number "+str(self)
        assert hasattr(elem, "num"), "cannot compare elements without element number "+str(elem)

    def __eq__(self, elem):
        if id(self) == id(elem):
            return True
        self._comparable_check(elem)
        if self.etype != elem.etype:
            return False
        if self.num.num != elem.num.num:
            return False
        return self.parent == elem.parent

    def __ne__(self, elem):
        return not self == elem

    def _lt_core(self, elem):
        if self.etype == elem.etype:
            return self.num.num < elem.num.num
        raise HieralchyError(
            self.lawdata,
            "Unexpected element occured in the same layer "+str(self.etype)+" "+str(elem.etype)
            )
    def __lt__(self, elem):
        self._comparable_check(elem)
        if self.parent == elem.parent:
            return self._lt_core(elem)
        if self.parent < elem.parent:
            return True
        elif self.parent >= elem.parent:
            return False
        raise Exception("Unexpected error in __lt__")

    def __le__(self, elem):
        if self == elem:
            return True
        return self < elem

    def __gt__(etype):
        return not self <= elem

    def __ge__(etype):
        return not self < elem

class RootExpansion(object):
    def __init__(self, lawdata):
        self.parent = None
        self._lawdata = lawdata
        self._num = None
        self._children = None
        self._text = None

    # 親から子を生成する場合は__init__を直接呼ばずにこちらで初期化する
    @classmethod
    def inheritance(cls, parent):
        raise Exception("You cannot call inheritance by root class "+str(cls.__name__))

    @property
    def lawdata(self):
        return self._lawdata

    @lawdata.setter
    def lawdata(self, lawdata):
        assert issubclass(lawdata.__class__, LawData), "Lawdata must be supplied as a subclass of LawData."
        self._lawdata = lawdata 

    @classmethod
    def is_root(cls):
        return True

    def __str__(self):
        return self.lawdata.name+self.name





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
