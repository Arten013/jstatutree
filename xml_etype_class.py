import etype_class
from jstatutree import ElementNumber
from myexceptions import LawElementNumberError

def get_text(b, e_val):
    if b is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

class XMLExpansion(object):
    @classmethod
    def inheritance(cls, parent, root):
        child = super(XMLExpansion, cls).inheritance(parent)
        child.root = root
        return child

    def _read_children_list(self):
        for f in list(self.root):
            if f.tag not in globals():
                continue
            yield globals()[f.tag].inheritance(self, f)

    def _read_num(self):
        numstr = self.root.attrib.get('Num', None)
        if numstr is None:
            return ElementNumber(1)
        try:
            return ElementNumber(numstr)
        except LawElementNumberError as e:
            raise LawElementNumberError(self.lawdata, **e.__dict__)

    def _read_text(self):
        return get_text(self.root, "")

class Law(XMLExpansion, etype_class.Law):
    pass

class LawBody(XMLExpansion, etype_class.LawBody):
    pass

class MainProvision(XMLExpansion, etype_class.MainProvision):
    pass

class Part(XMLExpansion, etype_class.Part):
    pass

class Chapter(XMLExpansion, etype_class.Chapter):
    pass

class Section(XMLExpansion, etype_class.Section):
    pass

class Subsection(XMLExpansion, etype_class.Subsection):
    pass

class Division(XMLExpansion, etype_class.Division):
    pass

class Article(XMLExpansion, etype_class.Article):
    pass

class ArticleCaption(XMLExpansion, etype_class.ArticleCaption):
    pass

class Paragraph(XMLExpansion, etype_class.Paragraph):
    pass

class ParagraphSentence(XMLExpansion, etype_class.ParagraphSentence):
    pass

class ParagraphCaption(XMLExpansion, etype_class.ParagraphCaption):
    pass

class Item(XMLExpansion, etype_class.Item):
    pass

class ItemSentence(XMLExpansion, etype_class.ItemSentence):
    pass

class Subitem1(XMLExpansion, etype_class.Subitem1):
    pass

class Subitem1Sentence(XMLExpansion, etype_class.Subitem1Sentence):
    pass

class Subitem2(XMLExpansion, etype_class.Subitem2):
    pass

class Subitem2Sentence(XMLExpansion, etype_class.Subitem2Sentence):
    pass

class Subitem3(XMLExpansion, etype_class.Subitem3):
    pass

class Subitem3Sentence(XMLExpansion, etype_class.Subitem3Sentence):
    pass

class Subitem4(XMLExpansion, etype_class.Subitem4):
    pass

class Subitem4Sentence(XMLExpansion, etype_class.Subitem4Sentence):
    pass

class Subitem5(XMLExpansion, etype_class.Subitem5):
    pass

class Subitem5Sentence(XMLExpansion, etype_class.Subitem5Sentence):
    pass

class Sentence(XMLExpansion, etype_class.Sentence):
    pass