from .element import Element
from .lawdata import ElementNumber, LawData
import re
from pathlib import Path

def get_etypes(name=None):
    if name:
        return ETYPES_DICT.get(name, UnknownElement)
    else:
        return ETYPES

def element_factory(name, *args, **kwargs):
    return get_etypes(name)(*args, **kwargs)

def sort_etypes(etypes, *args, **kwargs):
    return sorted(etypes, key=lambda x: (x.LEVEL, x.SUBLEVEL), *args, **kwargs)

_code2jname_ptn = [re.compile('\d+'), re.compile('(?P<etype>.+?)\((?P<num>\d+(:?\.\d+)?)\)$')]
def code2jname(code):
    jname = ''
    for part in Path(code).parts:
        if re.match(_code2jname_ptn[0], part):
            continue
        m = re.match(_code2jname_ptn[1], part)
        if m:
            etype = ETYPES_DICT.get(m.group('etype'))
            elem_num = ElementNumber(float(m.group('num')))
            num = elem_num.main_num
            branch_nums = list(map(str, elem_num.branch_nums))
            branch = 'の'+'の'.join(branch_nums) if len(branch_nums) else ''
            if len(etype.JNAME):
                jname += etype.JNAME.format(num=num, branch=branch)
    return jname

def is_item(elem):
    return elem.CATEGORY == CATEGORY_MINOR_CLAUSE \
             and 'Item' in elem.etype

## Category Enums ##
CATEGORY_UNKNOWN = -1
CATEGORY_ROOT = 0
CATEGORY_META = 1
CATEGORY_PROVISION = 2
CATEGORY_MAJOR_CLAUSE = 3
CATEGORY_MINOR_CLAUSE = 4
CATEGORY_CAPTION = 5
CATEGORY_TEXT = 6
CATEGORY_SENTENCE = 7
    
class UnknownElement(Element):
    LEVEL = 0
    PARENT_CANDIDATES = ()
    CATEGORY = CATEGORY_UNKNOWN
    
    @property
    def etype(self):
        return 'UNK'

class Law(Element):
    LEVEL = 0
    PARENT_CANDIDATES = ()
    CATEGORY = CATEGORY_ROOT

class LawBody(Element):
    LEVEL = Law.LEVEL + 1
    PARENT_CANDIDATES = (Law,)
    CATEGORY = CATEGORY_META

class MainProvision(Element):
    LEVEL = LawBody.LEVEL + 1
    PARENT_CANDIDATES = (LawBody,)
    CATEGORY = CATEGORY_PROVISION

class Part(Element):
    LEVEL = MainProvision.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision,)
    JNAME = "第{num}編"
    CATEGORY = CATEGORY_MAJOR_CLAUSE

class Chapter(Element):
    LEVEL = Part.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Part)
    JNAME = "第{num}章"
    CATEGORY = CATEGORY_MAJOR_CLAUSE

class Section(Element):
    LEVEL = Chapter.LEVEL + 1
    PARENT_CANDIDATES = (Chapter,)
    JNAME = "第{num}節"
    CATEGORY = CATEGORY_MAJOR_CLAUSE

class Subsection(Element):
    LEVEL = Section.LEVEL + 1
    PARENT_CANDIDATES = (Section,)
    JNAME = "第{num}款"
    CATEGORY = CATEGORY_MAJOR_CLAUSE

class Division(Element):
    LEVEL = Subsection.LEVEL + 1
    PARENT_CANDIDATES = (Subsection,)
    JNAME = "第{num}目"
    CATEGORY = CATEGORY_MAJOR_CLAUSE

class Article(Element):
    LEVEL = Division.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Part, Chapter, Section, Subsection, Division)
    JNAME = "第{num}条{branch}"
    CATEGORY = CATEGORY_MINOR_CLAUSE

class ArticleCaption(Element):
    LEVEL = Article.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Article,)
    JNAME = "条見出し"
    CATEGORY = CATEGORY_CAPTION

class Paragraph(Element):
    LEVEL = Article.LEVEL + 1
    PARENT_CANDIDATES = (MainProvision, Article)
    JNAME = "第{num}項"
    CATEGORY = CATEGORY_MINOR_CLAUSE

class ParagraphCaption(Element):
    LEVEL = Paragraph.LEVEL + 1
    SUBLEVEL = -2
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "項見出し"
    CATEGORY = CATEGORY_CAPTION

class ParagraphSentence(Element):
    LEVEL = Paragraph.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Paragraph,)
    CATEGORY = CATEGORY_TEXT

class Item(Element):
    LEVEL = Paragraph.LEVEL + 1
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "第{num}号{branch}"
    CATEGORY = CATEGORY_MINOR_CLAUSE

class ItemSentence(Element):
    LEVEL = Item.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Item,)
    CATEGORY = CATEGORY_TEXT

class Subitem1(Element):
    LEVEL = Item.LEVEL + 1
    PARENT_CANDIDATES = (Item,)
    JNAME = "{num}号細分{branch}"
    CATEGORY = CATEGORY_MINOR_CLAUSE

class Subitem1Sentence(Element):
    LEVEL = Subitem1.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem1,)
    CATEGORY = CATEGORY_TEXT

class Subitem2(Element):
    LEVEL = Subitem1.LEVEL + 1
    PARENT_CANDIDATES = (Subitem1,)
    JNAME = "{num}号細々分{branch}"
    CATEGORY = CATEGORY_MINOR_CLAUSE

class Subitem2Sentence(Element):
    LEVEL = Subitem2.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem2,)
    CATEGORY = CATEGORY_TEXT

class Subitem3(Element):
    LEVEL = Subitem2.LEVEL + 1
    PARENT_CANDIDATES = (Subitem2,)
    JNAME = "{num}号細々々分{branch}"
    CATEGORY = CATEGORY_MINOR_CLAUSE

class Subitem3Sentence(Element):
    LEVEL = Subitem3.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem3,)
    CATEGORY = CATEGORY_TEXT

class Subitem4(Element): 
    LEVEL = Subitem3.LEVEL + 1
    PARENT_CANDIDATES = (Subitem3,)
    JNAME = "{num}号細々々々分{branch}"
    CATEGORY = CATEGORY_MINOR_CLAUSE

class Subitem4Sentence(Element):
    LEVEL = Subitem4.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem4,)
    CATEGORY = CATEGORY_TEXT

class Subitem5(Element):
    LEVEL = Subitem4.LEVEL + 1
    PARENT_CANDIDATES = (Subitem4,)
    JNAME = "{num}号細々々々々分{branch}"
    CATEGORY = CATEGORY_MINOR_CLAUSE
    
class Subitem5Sentence(Element):
    LEVEL = Subitem5.LEVEL + 1
    SUBLEVEL = -1
    PARENT_CANDIDATES = (Subitem5,)
    CATEGORY = CATEGORY_TEXT

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
    CATEGORY = CATEGORY_META

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
    CATEGORY = CATEGORY_SENTENCE

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

_etype_ptn = re.compile('[^()]+')
def code2etype(code):
    return _etype_ptn.match(Path(code).name).group(0)