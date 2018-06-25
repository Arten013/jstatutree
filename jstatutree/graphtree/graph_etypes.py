import sys, os
from jstatutree import etypes
from jstatutree.lawdata import ElementNumber
from jstatutree.myexceptions import LawElementNumberError

def get_text(b, e_val):
    if b is not None and b.text is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

def get_etypes():
    return etypes.get_etypes_core(globals())

class XMLExpansion(object):
    @classmethod
    def convert(cls, *args, **kwargs):
        raise Exception("Cannot convert from other tree elements to xml tree elements.")

    @classmethod
    def vnode_inheritance(cls, parent):
        return cls.inheritance(parent, parent.root, 0, error_ok=True)

    @classmethod
    def inheritance(cls, parent, root, auto_index, error_ok=False):
        child = super(XMLExpansion, cls).inheritance(parent, error_ok)
        child.root = root
        child.num = ElementNumber(auto_index)
        return child

    def _read_children_list(self):
        auto_index = dict()
        for f in list(self.root):
            if f.tag not in globals():
                continue
            auto_index[f.tag] = auto_index.get(f.tag, 0) + 1
            yield globals()[f.tag].inheritance(self, f, auto_index[f.tag])

    @property
    def num(self):
        return super().num

    @num.setter
    def num(self, auto_index):
        if self._num is None:
            self._num = self._read_num()
            if self._num is None:
                self._num = auto_index

    def _read_num(self):
        numstr = self.root.attrib.get('Num', None)
        if numstr is None:
            return None
        try:
            return ElementNumber(numstr)
        except LawElementNumberError as e:
            raise LawElementNumberError(self.lawdata, **e.__dict__)

    def _read_text(self):
        return get_text(self.root, "")

class Law(XMLExpansion, etypes.Law):
    pass

class LawBody(XMLExpansion, etypes.LawBody):
    pass

class MainProvision(XMLExpansion, etypes.MainProvision):
    pass

class Part(XMLExpansion, etypes.Part):
    pass

class Chapter(XMLExpansion, etypes.Chapter):
    pass

class Section(XMLExpansion, etypes.Section):
    pass

class Subsection(XMLExpansion, etypes.Subsection):
    pass

class Division(XMLExpansion, etypes.Division):
    pass

class Article(XMLExpansion, etypes.Article):
    pass

class ArticleCaption(XMLExpansion, etypes.ArticleCaption):
    pass

class Paragraph(XMLExpansion, etypes.Paragraph):
    pass

class ParagraphSentence(XMLExpansion, etypes.ParagraphSentence):
    pass

class ParagraphCaption(XMLExpansion, etypes.ParagraphCaption):
    pass

class Item(XMLExpansion, etypes.Item):
    pass

class ItemSentence(XMLExpansion, etypes.ItemSentence):
    pass

class Subitem1(XMLExpansion, etypes.Subitem1):
    pass

class Subitem1Sentence(XMLExpansion, etypes.Subitem1Sentence):
    pass

class Subitem2(XMLExpansion, etypes.Subitem2):
    pass

class Subitem2Sentence(XMLExpansion, etypes.Subitem2Sentence):
    pass

class Subitem3(XMLExpansion, etypes.Subitem3):
    pass

class Subitem3Sentence(XMLExpansion, etypes.Subitem3Sentence):
    pass

class Subitem4(XMLExpansion, etypes.Subitem4):
    pass

class Subitem4Sentence(XMLExpansion, etypes.Subitem4Sentence):
    pass

class Subitem5(XMLExpansion, etypes.Subitem5):
    pass

class Subitem5Sentence(XMLExpansion, etypes.Subitem5Sentence):
    pass

class Sentence(XMLExpansion, etypes.Sentence):
    pass