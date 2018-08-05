import sys, os
from jstatutree import etypes
from jstatutree.lawdata import ElementNumber
from jstatutree.myexceptions import LawElementNumberError

def get_etypes():
    return etypes.get_etypes_core(globals())

def convert_recursively(src_root):
    return etypes.convert_recursively(src_root, _tar_root=None, etypes_dict=globals())

class N4JExpansion(object):
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
    def get_virtual_node(self, target_etype):
        vnode = target_etype.vnode_inheritance(self)
        vnode._is_vnode=True
        vnode._children = self._children
        #print("generate vnode:", vnode, vnode.etype.__name__)
        #print("from:", self, self.etype.__name__)
        return vnode

    @classmethod
    def vnode_inheritance(cls, parent):
        tmp_parent = parent
        while not hasattr(tmp_parent, 'node'):
            assert tmp_parent.parent is not None, 'Unexpected Error'
            tmp_parent = tmp_parent.parent
        return cls.inheritance(tmp_parent.node, parent, error_ok=True)
    # 親から子を生成する場合は__init__を直接呼ばずにこちらで初期化する
    @classmethod
    def inheritance(cls, node, parent, error_ok=False):
        if not error_ok and not isinstance(parent, cls.PARENT_CANDIDATES):
            raise HieralchyError(
                parent.lawdata,
                "invalid hieralchy "+parent.etype.__name__ + " -> " + cls.__name__
            )
        child = cls(parent)
        child.node = node
        return child

    # load node properties from database when it called
    @property
    def properties(self):
        return self.node

    # read children nodes from database
    def _read_children_list(self):
        for rel in self.node.relationships.all():
            if rel.type != 'CHILD_OF':
                continue
            child_node = rel.end
            child = globals()[child_node.properties["etype"]].inheritance(child_node, self)

    def _read_num(self):
        return self.properties['num']

    def _read_text(self):
        return self.properties.get('text','')

class Law(N4JExpansion, etypes.Law):
    def __init__(self, lawdata):
        super().__init__(lawdata)
        self.node = lawdata.node

class LawBody(N4JExpansion, etypes.LawBody):
    pass

class MainProvision(N4JExpansion, etypes.MainProvision):
    pass

class Part(N4JExpansion, etypes.Part):
    pass

class Chapter(N4JExpansion, etypes.Chapter):
    pass

class Section(N4JExpansion, etypes.Section):
    pass

class Subsection(N4JExpansion, etypes.Subsection):
    pass

class Division(N4JExpansion, etypes.Division):
    pass

class Article(N4JExpansion, etypes.Article):
    pass

class ArticleCaption(N4JExpansion, etypes.ArticleCaption):
    pass

class Paragraph(N4JExpansion, etypes.Paragraph):
    pass

class ParagraphSentence(N4JExpansion, etypes.ParagraphSentence):
    pass

class ParagraphCaption(N4JExpansion, etypes.ParagraphCaption):
    pass

class Item(N4JExpansion, etypes.Item):
    pass

class ItemSentence(N4JExpansion, etypes.ItemSentence):
    pass

class Subitem1(N4JExpansion, etypes.Subitem1):
    pass

class Subitem1Sentence(N4JExpansion, etypes.Subitem1Sentence):
    pass

class Subitem2(N4JExpansion, etypes.Subitem2):
    pass

class Subitem2Sentence(N4JExpansion, etypes.Subitem2Sentence):
    pass

class Subitem3(N4JExpansion, etypes.Subitem3):
    pass

class Subitem3Sentence(N4JExpansion, etypes.Subitem3Sentence):
    pass

class Subitem4(N4JExpansion, etypes.Subitem4):
    pass

class Subitem4Sentence(N4JExpansion, etypes.Subitem4Sentence):
    pass

class Subitem5(N4JExpansion, etypes.Subitem5):
    pass

class Subitem5Sentence(N4JExpansion, etypes.Subitem5Sentence):
    pass

class Sentence(N4JExpansion, etypes.Sentence):
    pass
