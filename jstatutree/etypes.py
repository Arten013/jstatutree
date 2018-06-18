from abc import abstractmethod
import unicodedata
from .myexceptions import *
from .lawdata import ElementNumber

# 要素の基底クラス
class TreeElement(object):
    LEVEL = 0
    SUBLEVEL = 0
    PARENT_CANDIDATES = ()
    CHILDREN_PATTERNS = ()
    JNAME = ""

    def __init__(self, parent=None):
        self.parent = parent
        self._num = None
        self._children = None
        self._text = None

    def get_virtual_node(self, target_etype):
        vnode = target_etype.vnode_inheritance(self)
        vnode._is_vnode=True
        vnode._children = self._children
        #print("generate vnode:", vnode, vnode.etype.__name__)
        #print("from:", self, self.etype.__name__)
        return vnode

    @classmethod
    def vnode_inheritance(cls, parent):
        return cls.inheritance(parent, error_ok=True)

    # 親から子を生成する場合は__init__を直接呼ばずにこちらで初期化する
    @classmethod
    def inheritance(cls, parent, error_ok=False):
        if not error_ok and not isinstance(parent, cls.PARENT_CANDIDATES):
            raise HieralchyError(
                parent.lawdata,
                "invalid hieralchy "+parent.etype.__name__ + " -> " + cls.__name__
            )
        child = cls(parent)
        return child

    @property
    def is_vnode(self):
        if "_is_vnode" not in self.__dict__:
            self._is_vnode = False
        return self._is_vnode
    
    @property
    def code(self):
        if "_code" not in self.__dict__:
            nums = [self.num.main_num] + self.num.branch_nums
            self._code = self.parent.code + "/{etype}({num})".format(etype=self.etype.__name__, num="_".join([str(n) for n in nums]))
        return self._code

    # 呼び出し時に読み出す(children, name, text)
    @property
    def children(self):
        if self._children is None:
            self._children = self._find_children()
        return self._children

    @property
    def num(self):
        if self.is_vnode:
            self._num = ElementNumber("0")
        elif self._num is None:
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
        if self.is_vnode:
            return self.parent.name
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
        return ElementNumber("1")

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

    def copy(self, etype=None):
        etype = self.etype if etype is None else etype
        assert etype.__name__ == self.etype.__name__, "Cannot copy from different etype."
        copy = etype()

        # todo: コピーするべきものをコピーする

        return copy

    def depth_first_search(self, target_etype, valid_vnode=False):
        assert issubclass(target_etype, TreeElement), "target_etype must be a subclass of TreeElement (given {})".format(target_etype.__class__.__name__)
        #print(target_etype.__name__, target_etype.LEVEL, "vs.", self.etype.__name__, self.etype.LEVEL)
        if target_etype.LEVEL == self.etype.LEVEL:
            if target_etype.SUBLEVEL == self.etype.SUBLEVEL:
                yield self
                return
        if target_etype.LEVEL < self.etype.LEVEL:
            return
        elif target_etype.LEVEL >= self.etype.LEVEL:
            yielded_flag = False
            iter_flag = False
            for child in sorted(self.children.values()):
                iter_flag = True
                if child.etype.LEVEL < target_etype.LEVEL:
                    yield from child.depth_first_search(target_etype, valid_vnode)
                    yielded_flag = True
                elif child.etype.LEVEL == target_etype.LEVEL:
                    if child.SUBLEVEL == target_etype.SUBLEVEL:
                        yield child
                        yielded_flag = True
                else:
                    yielded_flag = True
                    if valid_vnode:
                        yield self.get_virtual_node(target_etype)
                        return
                    yield self
            if iter_flag and not yielded_flag and valid_vnode:
                yield self.get_virtual_node(target_etype)
                return

    def depth_first_iteration(self):
        yield self
        for child in sorted(self.children.values()):
            yield from child.depth_first_iteration()

    def iter_sentences(self):
        for child in self.depth_first_iteration():
            if child.etype.__name__ == "Sentence":
                yield child.text
                
    def iter_texts(self):
        for child in self.depth_first_iteration():
            yield child.text

    def delete_values_recursively(self, *value_tags):
        for elem in self.depth_first_iteration():
            elem.delete_values(*value_tags)

    def delete_values(self, *value_tags):
        for vt in value_tags:
            if "_"+vt in self.__dict__:
                del self.__dict__["_"+vt]
            if vt in self.__dict__:
                del self.__dict__[vt]

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

    def __lt__(self, elem):
        self._comparable_check(elem)
        if self.etype.LEVEL > elem.etype.LEVEL:
            return self.parent > elem
        elif self.etype.LEVEL < elem.etype.LEVEL:
            return self > elem.parent
        elif self.parent == elem.parent:
            if self.etype.LEVEL != elem.etype.LEVEL:
                raise HieralchyError(
                    self.lawdata,
                    "Unexpected element occured in the same layer "+str(self.etype)+" "+str(elem.etype)
                    )
            if self.etype.SUBLEVEL == self.etype.SUBLEVEL:
                return self.num.num < elem.num.num
            else:
                return self.etype.SUBLEVEL < self.etype.SUBLEVEL
        return self.parent < elem.parent

    def __le__(self, elem):
        if self == elem:
            return True
        return self < elem

    def __gt__(self, elem):
        return not self <= elem

    def __ge__(self, elem):
        return not self < elem

    def __hash__(self):
        return hash(self.code)

    # "X法第n条第m項"のように出力
    def __str__(self):
        if self.is_vnode:
            return str(self.parent)
        return str(self.parent)+str(self.name)

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

    @property
    def code(self):
        if "_code" not in self.__dict__:
            nums = [self.num.main_num] + self.num.branch_nums
            self._code = self.lawdata.code + "/{etype}({num})".format(etype=self.etype.__name__, num="_".join([str(n) for n in nums]))
        return self._code

def get_etypes():
    return get_etypes_core(globals_dict=globals())

def get_etypes_core(globals_dict):
    etypes = []
    root = None
    for etype_name, etype_cls in globals_dict.items():
        if type(etype_cls) is not type or not hasattr(etype_cls, "etype") or "Expansion" in etype_name:
            continue
        if etype_cls == TreeElement:
            continue
        if etype_cls.is_root():
            assert root is None, "root elem has to be unique."
            root = etype_cls
        else:
            etypes.append(etype_cls)
    assert root is not None, "No root has been defined."+str(etypes)

    return [root] + etypes

def sort_etypes(etypes, *args, **kwargs):
    return sorted(etypes, key=lambda x: (x.LEVEL, x.SUBLEVEL), *args, **kwargs)

class Law(RootExpansion, TreeElement):
    LEVEL = 0
    PARENT_CANDIDATES = ()

class LawBody(TreeElement):
    LEVEL = Law.LEVEL + 1
    PARENT_CANDIDATES = (Law,)

class MainProvision(TreeElement):
    LEVEL = LawBody.LEVEL + 1
    PARENT_CANDIDATES = (LawBody,)

class Part(TreeElement):
    LEVEL = MainProvision.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision,)
    JNAME = "第{num}編"

class Chapter(TreeElement):
    LEVEL = Part.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Part)
    JNAME = "第{num}章"

class Section(TreeElement):
    LEVEL = Chapter.LEVEL + 1
    PARENT_CANDIDATES = (Chapter,)
    JNAME = "第{num}節"

class Subsection(TreeElement):
    LEVEL = Section.LEVEL + 1
    PARENT_CANDIDATES = (Section,)
    JNAME = "第{num}款"

class Division(TreeElement):
    LEVEL = Subsection.LEVEL + 1
    PARENT_CANDIDATES = (Subsection,)
    JNAME = "第{num}目"

class Article(TreeElement):
    LEVEL = Division.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Part, Chapter, Section, Subsection, Division)
    JNAME = "第{num}条{branch}"

class ArticleCaption(TreeElement):
    LEVEL = Article.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Article,)
    JNAME = "条見出し"

class Paragraph(TreeElement):
    LEVEL = Article.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Article)
    JNAME = "第{num}項"

class ParagraphCaption(TreeElement):
    LEVEL = Paragraph.LEVEL + 1
    SUBLEVEL = -2
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "項見出し"

class ParagraphSentence(TreeElement):
    LEVEL = Paragraph.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Paragraph,)

class Item(TreeElement):
    LEVEL = Paragraph.LEVEL + 1
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "第{num}号{branch}"

class ItemSentence(TreeElement):
    LEVEL = Item.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Item,)

class Subitem1(TreeElement):
    LEVEL = Item.LEVEL + 1
    PARENT_CANDIDATES = (Item,)
    JNAME = "{num}号細分{branch}"

class Subitem1Sentence(TreeElement):
    LEVEL = Subitem1.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem1,)

class Subitem2(TreeElement):
    LEVEL = Subitem1.LEVEL + 1
    PARENT_CANDIDATES = (Subitem1,)
    JNAME = "{num}号細々分{branch}"

class Subitem2Sentence(TreeElement):
    LEVEL = Subitem2.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem2,)

class Subitem3(TreeElement):
    LEVEL = Subitem2.LEVEL + 1
    PARENT_CANDIDATES = (Subitem2,)
    JNAME = "{num}号細々々分{branch}"

class Subitem3Sentence(TreeElement):
    LEVEL = Subitem3.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem3,)

class Subitem4(TreeElement): 
    LEVEL = Subitem3.LEVEL + 1
    PARENT_CANDIDATES = (Subitem3,)
    JNAME = "{num}号細々々々分{branch}"

class Subitem4Sentence(TreeElement):
    LEVEL = Subitem4.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem4,)

class Subitem5(TreeElement):
    LEVEL = Subitem4.LEVEL + 1
    PARENT_CANDIDATES = (Subitem4,)
    JNAME = "{num}号細々々々々分{branch}"

class Subitem5Sentence(TreeElement):
    LEVEL = Subitem5.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem5,)

class Sentence(TreeElement):
    LEVEL = Subitem5.LEVEL + 1
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