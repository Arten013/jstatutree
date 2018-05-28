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

class Law(TreeElement):
    PARENT_CANDIDATES = ()

class LawBody(TreeElement):
    PARENT_CANDIDATES = (Law,)

class MainProvision(TreeElement):
    PARENT_CANDIDATES = (LawBody,)

class Part(TreeElement):
    PARENT_CANDIDATES = (MainProvision,)
    JNAME = "第{num}編"

class Chapter(TreeElement):
    PARENT_CANDIDATES = (MainProvision, Part)
    JNAME = "第{num}章"

class Section(TreeElement):
    PARENT_CANDIDATES = (Chapter,)
    JNAME = "第{num}節"

class Subsection(TreeElement):
    PARENT_CANDIDATES = (Section,)
    JNAME = "第{num}款"

class Division(TreeElement):
    PARENT_CANDIDATES = (Subsection,)
    JNAME = "第{num}目"

class Article(TreeElement):
    PARENT_CANDIDATES = (MainProvision, Part, Chapter, Section, Subsection, Division)
    JNAME = "第{num}条{branch}"

class ArticleCaption(TreeElement):
    PARENT_CANDIDATES = (Article,)
    JNAME = "条見出し"

class Paragraph(TreeElement):
    PARENT_CANDIDATES = (MainProvision, Article)
    JNAME = "第{num}項"

class ParagraphSentence(TreeElement):
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "第{num}文"

class ParagraphCaption(TreeElement):
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "項見出し"

class Item(TreeElement):
    PARENT_CANDIDATES = (Article, Paragraph)
    JNAME = "第{num}号{branch}"

class ItemSentence(TreeElement):
    PARENT_CANDIDATES = (Item,)

class Subitem1(TreeElement):
    PARENT_CANDIDATES = (Item,)
    JNAME = "{num}号細分{branch}"

class Subitem1Sentence(TreeElement):
    PARENT_CANDIDATES = (Item,)

class Subitem2(TreeElement):
    PARENT_CANDIDATES = (Subitem1,)
    JNAME = "{num}号細々分{branch}"

class Subitem2Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem1,)

class Subitem3(TreeElement):
    PARENT_CANDIDATES = (Subitem2,)
    JNAME = "{num}号細々々分{branch}"

class Subitem3Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem2,)

class Subitem4(TreeElement):
    PARENT_CANDIDATES = (Subitem3,)
    JNAME = "{num}号細々々々分{branch}"

class Subitem4Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem3,)

class Subitem5(TreeElement):
    PARENT_CANDIDATES = (Subitem4,)
    JNAME = "{num}号細々々々々分{branch}"

class Subitem5Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem4,)

class Sentence(TreeElement):
    PARENT_CANDIDATES = (
        ParagraphSentence, 
        ItemSentence, 
        Subitem1Sentence, 
        Subitem2Sentence, 
        Subitem3Sentence, 
        Subitem4Sentence, 
        Subitem5Sentence
        )
    JNAME = "第{num}文"

