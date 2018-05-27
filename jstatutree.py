class SourceInterface(object):
    def open(self):
        pass`1

# 法令文書を扱うためのTree
class JpnStatuTree(object):
    def __init__(self, source):
        self.source = source

    def __str__(self):
        return "{name} ({num})".format(name=self.name, num=self.num)

    def is_reiki(self):
        return True if re.search("(?:条例|規則)", self.lawnum) else False

    def count_elems(self, error_ok=False):
        c = Counter()
        for ce in self.root.iter_descendants(error_ok=error_ok):
                c.update({ce.__class__.__name__: 1})
        return c

class LawData(object):
    def __init__(self):
        self._name = None
        self._lawnum = None

    @property
    def name(self):
        return "UNK" if self._name is None else self._name

    @name.setter
    def name(self, name):
        return self._name = name

    @property
    def lawnum(self):
        return "UNK" if self._num is None else self._num

    @lawnum.setter
    def lawnum(self, lawnum):
        return self._lawnum = lawnum

# 例規のメタデータ
class ReikiData(object):
    def __init__(self):
        super().__init__()
        self._code = None
        self._id = None
        self.prefecture_code = 0
        self.municipality_code = 0
        self.file_code = 0

    @property
    def code(self):
        if self._code is None:
            self._code = "{0:02}/{1:06}/{2:04}".format(
                int(self.prefecture_code), 
                int(self.municipality_code), 
                int(self.file_code)
                )
        return self._code

    @property
    def id(self):
        if self._id is None:
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
        if self.num == 0:
            return JNAME
        else:
            return JNAME.format(num=self.num)

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

    @abstractmethod
    def _read_metadata(self):


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
        self.etype = etype
        if isinstance(arg, int):
            self.num = Decimal(arg)     
        if isinstance(arg, str):
            self.num = process_branch_num_str(arg)
        elif isinstance(arg, (Decimal,)):
            self.num = arg
        elif isinstance(arg, (ElementNumber,)):
            self.num = arg.num
        else:
            raise TypeError("Invalid type for init ElementNumber: {}".format(arg.__class__.__name__))

    def __float__(self):
        return float(self.num)

    def __str__(self):
        if self._str is not None
            self._str = str(self.num.quantize(Decimal('1')))
            num = self.num - self.num.quantize(Decimal('1'))
            while num.quantize(Decimal('1')) != Decimal(0):
                self.num *= 100
                self._str += "の"+str(num.quantize(Decimal('1')))
                num = num - num.quantize(Decimal('1'))
        return self._str

    def str_to_decimal(self, strnum):
        if re.match("^[0-9]+(?:_[0-9]+)*$", strnum) is None:
            raise LawElementNumberError(error_detail="Invalid Format {}".format(strnum))
        num = Decimal(0)
        mul = Decimal(1)
        for n in strnum.split("_"):
            num += Decimal(n) * mul
            mul /= Decimal(1000)
        return num

class Law(TreeElement):
    PARENT_CANDIDATES = ()
    JNAME = ""

class LawBody(TreeElement):
    PARENT_CANDIDATES = ("Law")
    JNAME = ""

class MainProvision(ProvBase, ETreeLawElementBase):
    PARENT_CANDIDATES = ("")
    JNAME = ""

class Part(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision,)

class Chapter(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, Part)

class Section(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Chapter,)

class Subsection(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Section,)

class Division(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Subsection,)

class Article(BasicElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, SupplProvision, Part, Chapter, Section, Subsection, Division)

class ETreeSentenceBase(SentenceBase, ETreeLawElementBase):
    def inheritance(self, root):
        self.root = root
        super().inheritance()

    def extract_text(self):
        return list(get_text(s, "") for s in self.root.findall('./Sentence'.format(self.__class__.__name__)))

class ArticleCaption(CaptionBase, ETreeSentenceBase):
    PARENT_CANDIDATES = (Article,)
    def extract_text(self):
        return [get_text(self.root, '')]

class Paragraph(BasicElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, SupplProvision, Article)

class ParagraphSentence(ETreeSentenceBase):
    PARENT_CANDIDATES = (Paragraph,)

class Item(ItemBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Article, Paragraph)

class ItemSentence(ETreeSentenceBase):
    PARENT_CANDIDATES = (Item,)

class Subitem1(Item):
    PARENT_CANDIDATES = (Item,)

class Subitem1Sentence(ItemSentence):
    PARENT_CANDIDATES = (Item,)

class Subitem2(Item):
    PARENT_CANDIDATES = (Subitem1,)

class Subitem2Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem1,)

class Subitem3(Item):
    PARENT_CANDIDATES = (Subitem2,)

class Subitem3Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem2,)

class Subitem4(Item):
    PARENT_CANDIDATES = (Subitem3,)

class Subitem4Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem3,)

class Subitem5(Item):
    PARENT_CANDIDATES = (Subitem4,)

class Subitem5Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem4,)
