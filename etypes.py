from jstatutree import TreeElement, RootExpansion

class Law(RootExpansion, TreeElement):
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

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Paragraph,)):
            return True
        return super()._lt_core(elem)

class Paragraph(TreeElement):
    PARENT_CANDIDATES = (MainProvision, Article)
    JNAME = "第{num}項"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (ArticleCaption,)):
            return False
        return super()._lt_core(elem)

class ParagraphSentence(TreeElement):
    PARENT_CANDIDATES = (Paragraph,)

    def _lt_core(self, elem):
        if issubclass(elem.etype, (ParagraphCaption,)):
            return False
        if issubclass(elem.etype, (Item,)):
            return True
        return super()._lt_core(elem)

class ParagraphCaption(TreeElement):
    PARENT_CANDIDATES = (Paragraph,)
    JNAME = "項見出し"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (ParagraphSentence, Item)):
            return True
        return super()._lt_core(elem)

class Item(TreeElement):
    PARENT_CANDIDATES = (Article, Paragraph)
    JNAME = "第{num}号{branch}"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (ParagraphSentence, ParagraphCaption)):
            return False
        return super()._lt_core(elem)

class ItemSentence(TreeElement):
    PARENT_CANDIDATES = (Item,)

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem1)):
            return True
        return super()._lt_core(elem)

class Subitem1(TreeElement):
    PARENT_CANDIDATES = (Item,)
    JNAME = "{num}号細分{branch}"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (ItemSentence)):
            return False
        return super()._lt_core(elem)

class Subitem1Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem1,)

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem2)):
            return True
        return super()._lt_core(elem)

class Subitem2(TreeElement):
    PARENT_CANDIDATES = (Subitem1,)
    JNAME = "{num}号細々分{branch}"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem1Sentence)):
            return False
        return super()._lt_core(elem)

class Subitem2Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem2,)

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem3)):
            return True
        return super()._lt_core(elem)

class Subitem3(TreeElement):
    PARENT_CANDIDATES = (Subitem2,)
    JNAME = "{num}号細々々分{branch}"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem2Sentence)):
            return False
        return super()._lt_core(elem)

class Subitem3Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem3,)

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem4)):
            return True
        return super()._lt_core(elem)

class Subitem4(TreeElement):
    PARENT_CANDIDATES = (Subitem3,)
    JNAME = "{num}号細々々々分{branch}"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem3Sentence)):
            return False
        return super()._lt_core(elem)

class Subitem4Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem4,)

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem5)):
            return True
        return super()._lt_core(elem)

class Subitem5(TreeElement):
    PARENT_CANDIDATES = (Subitem4,)
    JNAME = "{num}号細々々々々分{branch}"

    def _lt_core(self, elem):
        if issubclass(elem.etype, (Subitem4Sentence)):
            return False
        return super()._lt_core(elem)

class Subitem5Sentence(TreeElement):
    PARENT_CANDIDATES = (Subitem5,)

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