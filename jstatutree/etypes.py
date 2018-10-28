from .element import Element
from .lawdata import ElementNumber, LawData

def get_etypes(name=None):
    if name:
        return ETYPES_DICT.get(name, UnknownElement)
    else:
        return ETYPES

def element_factory(name, *args, **kwargs):
    return get_etypes(name)(*args, **kwargs)

def sort_etypes(etypes, *args, **kwargs):
    return sorted(etypes, key=lambda x: (x.LEVEL, x.SUBLEVEL), *args, **kwargs)

class UnknownElement(Element):
    LEVEL = 0
    PARENT_CANDIDATES = ()

    @property
    def etype(self):
        return 'UNK'

class Law(Element):
    LEVEL = 0
    PARENT_CANDIDATES = ()

class LawBody(Element):
    LEVEL = Law.LEVEL + 1
    PARENT_CANDIDATES = (Law,)

class MainProvision(Element):
    LEVEL = LawBody.LEVEL + 1
    PARENT_CANDIDATES = (LawBody,)

class Part(Element):
    LEVEL = MainProvision.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision,)
    JNAME = "第{num}編"

class Chapter(Element):
    LEVEL = Part.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Part)
    JNAME = "第{num}章"

class Section(Element):
    LEVEL = Chapter.LEVEL + 1
    PARENT_CANDIDATES = (Chapter,)
    JNAME = "第{num}節"

class Subsection(Element):
    LEVEL = Section.LEVEL + 1
    PARENT_CANDIDATES = (Section,)
    JNAME = "第{num}款"

class Division(Element):
    LEVEL = Subsection.LEVEL + 1
    PARENT_CANDIDATES = (Subsection,)
    JNAME = "第{num}目"

class Article(Element):
    LEVEL = Division.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Part, Chapter, Section, Subsection, Division)
    JNAME = "第{num}条{branch}"

class ArticleCaption(Element):
    LEVEL = Article.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Article,)
    JNAME = "条見出し"

class Paragraph(Element):
    LEVEL = Article.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Article)
    JNAME = "第{num}項"

class ParagraphCaption(Element):
    LEVEL = Paragraph.LEVEL + 1
    SUBLEVEL = -2
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "項見出し"

class ParagraphSentence(Element):
    LEVEL = Paragraph.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Paragraph,)

class Item(Element):
    LEVEL = Paragraph.LEVEL + 1
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "第{num}号{branch}"

class ItemSentence(Element):
    LEVEL = Item.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Item,)

class Subitem1(Element):
    LEVEL = Item.LEVEL + 1
    PARENT_CANDIDATES = (Item,)
    JNAME = "{num}号細分{branch}"

class Subitem1Sentence(Element):
    LEVEL = Subitem1.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem1,)

class Subitem2(Element):
    LEVEL = Subitem1.LEVEL + 1
    PARENT_CANDIDATES = (Subitem1,)
    JNAME = "{num}号細々分{branch}"

class Subitem2Sentence(Element):
    LEVEL = Subitem2.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem2,)

class Subitem3(Element):
    LEVEL = Subitem2.LEVEL + 1
    PARENT_CANDIDATES = (Subitem2,)
    JNAME = "{num}号細々々分{branch}"

class Subitem3Sentence(Element):
    LEVEL = Subitem3.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem3,)

class Subitem4(Element): 
    LEVEL = Subitem3.LEVEL + 1
    PARENT_CANDIDATES = (Subitem3,)
    JNAME = "{num}号細々々々分{branch}"

class Subitem4Sentence(Element):
    LEVEL = Subitem4.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem4,)

class Subitem5(Element):
    LEVEL = Subitem4.LEVEL + 1
    PARENT_CANDIDATES = (Subitem4,)
    JNAME = "{num}号細々々々々分{branch}"

class Subitem5Sentence(Element):
    LEVEL = Subitem5.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem5,)

class Column(Element):
    LEVEL = Subitem5Sentence.LEVEL + 1
    PARENT_CANDIDATES = (
        ParagraphSentence, 
        ItemSentence, 
        Subitem1Sentence, 
        Subitem2Sentence, 
        Subitem3Sentence, 
        Subitem4Sentence, 
        Subitem5Sentence
        )

class Sentence(Element):
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

ETYPES = [
        Law,
        LawBody,
        MainProvision,
        Part,
        Chapter,
        Section,
        Subsection,
        Division,
        Article,
        ArticleCaption,
        Paragraph,
        ParagraphCaption,
        ParagraphSentence,
        Item,
        ItemSentence,
        Subitem1,
        Subitem1Sentence,
        Subitem2,
        Subitem2Sentence,
        Subitem3,
        Subitem3Sentence,
        Subitem4,
        Subitem4Sentence,
        Subitem5,
        Subitem5Sentence,
        Column,
        Sentence,
        ]
ETYPES_DICT = {e.__name__:e for e in ETYPES}

