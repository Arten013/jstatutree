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

def convert_recursively(src_root):
    return etypes.convert_recursively(src_root, _tar_root=None, etypes_dict=globals())

class MLExpansion(object):
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
    @property
    def db(self):
        return self.parent.db if "_db" not in self.__dict__ else self._db
    
    @db.setter
    def db(self, val):
        self._db = val

    def _read_children_list(self):
        raise Exception("Unexpected Error")

    def _read_num(self):
        raise Exception("Unexpected Error")

    def _read_text(self):
        return self.db["sentence"].get(self.code, "")

class Law(MLExpansion, etypes.Law):
    pass

class LawBody(MLExpansion, etypes.LawBody):
    pass

class MainProvision(MLExpansion, etypes.MainProvision):
    pass

class Part(MLExpansion, etypes.Part):
    pass

class Chapter(MLExpansion, etypes.Chapter):
    pass

class Section(MLExpansion, etypes.Section):
    pass

class Subsection(MLExpansion, etypes.Subsection):
    pass

class Division(MLExpansion, etypes.Division):
    pass

class Article(MLExpansion, etypes.Article):
    pass

class ArticleCaption(MLExpansion, etypes.ArticleCaption):
    pass

class Paragraph(MLExpansion, etypes.Paragraph):
    pass

class ParagraphSentence(MLExpansion, etypes.ParagraphSentence):
    pass

class ParagraphCaption(MLExpansion, etypes.ParagraphCaption):
    pass

class Item(MLExpansion, etypes.Item):
    pass

class ItemSentence(MLExpansion, etypes.ItemSentence):
    pass

class Subitem1(MLExpansion, etypes.Subitem1):
    pass

class Subitem1Sentence(MLExpansion, etypes.Subitem1Sentence):
    pass

class Subitem2(MLExpansion, etypes.Subitem2):
    pass

class Subitem2Sentence(MLExpansion, etypes.Subitem2Sentence):
    pass

class Subitem3(MLExpansion, etypes.Subitem3):
    pass

class Subitem3Sentence(MLExpansion, etypes.Subitem3Sentence):
    pass

class Subitem4(MLExpansion, etypes.Subitem4):
    pass

class Subitem4Sentence(MLExpansion, etypes.Subitem4Sentence):
    pass

class Subitem5(MLExpansion, etypes.Subitem5):
    pass

class Subitem5Sentence(MLExpansion, etypes.Subitem5Sentence):
    pass

class Sentence(MLExpansion, etypes.Sentence):
    pass
