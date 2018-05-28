from jstatutree import TreeElement

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
