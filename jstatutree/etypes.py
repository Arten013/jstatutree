from .tree_element import TreeElement as TreeElementBase
from .lawdata import ElementNumber, LawData

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

def convert_recursively(src_root, _tar_root=None, etypes_dict=None):
    etypes_dict = globals() if etypes_dict is None else etypes_dict
    tar_root = etypes_dict[src_root.etype.__name__].convert(src_root) if _tar_root is None else _tar_root
    tar_root._children = dict()
    for src_elem in src_root.children.values():
        new_etype = etypes_dict[src_elem.etype.__name__].convert(src_elem)
        new_etype.parent = tar_root
        tar_root.children[new_etype.name] = convert_recursively(src_elem, new_etype, etypes_dict)
    return tar_root

class TreeElement(TreeElementBase):
    def get_coherent_etype(self, etype):
        # print('get_coherent_etype: begin')
        etype = etype if isinstance(etype, str) else etype.__name__
        # print('get_coherent_etype: receive etype '+str(etype))
        for et in get_etypes():
            # print('get_coherent_etype: try ' +str(et))
            if et.__name__ == etype:
                # print('get_coherent_etype: return '+str(et))
                return et
        raise 'invalid etype '+etype

class RootExpansion(object):
    def __init__(self, lawdata):
        self.parent = None
        self._lawdata = lawdata
        self._num = ElementNumber("1")
        self._children = None
        self._text = None

    @classmethod
    def convert(cls, src_elem):
        tar_elem = cls(src_elem.lawdata)
        assert src_elem.num is not None, "Source etype must have num"
        tar_elem._num = src_elem.num
        tar_elem._text = src_elem.text
        tar_elem._children = dict()
        return tar_elem

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

class Column(TreeElement):
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
class Sentence(TreeElement):
    LEVEL = Column.LEVEL + 1
    PARENT_CANDIDATES = (
        Column,
        ParagraphSentence, 
        ItemSentence, 
        Subitem1Sentence, 
        Subitem2Sentence, 
        Subitem3Sentence, 
        Subitem4Sentence, 
        Subitem5Sentence
        )
    JNAME = "第{num}文"
