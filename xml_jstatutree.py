
def get_text(b, e_val):
    if b is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

class ReikiXMLReader(object):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.file = None

    def open(self):
        root_etree = ET.parse(self.path).getroot()
        root = Law(None)
        root.inheritance(root_etree)
        root.lawdata = self._get_lawdata(root_etree)
        return root

    def _get_lawdata(self, root_etree):
        lawdata = ReikiData()

        # reikicodeの設定
        p, file = os.path.split(self.path)
        lawdata.file_code = os.path.splitext(file)[0]
        p, lawdata.municipality_code = os.path.split(p)
        _, lawdata.prefecture_code = os.path.split(p)

        # nameの設定
        lawdata.name = get_text(self.root.find('Law/LawBody/LawTitle'), None)

        # lawnumの設定
        lawnum_text = get_text(self.root.find('Law/LawNum'), "")
        lawnum_text = kan_ara(unicodedata.normalize("NFKC", lawnum_text))
        lawdata.lawnum = None if len(lawnum_text) == 0 else lawnum_text

        return lawdata

class XMLExpansion(object):
    @classmethod
    def inheritance(cls, parent, root):
        child = super(XMLExpansion, cls).inheritance(parent)
        child.root = root
        return child

    def _read_children_list(self):
        for f in self.root.findall("./*"):
            if f.tag not in ETYPES:
                continue
            yield globals()[f.tag].inheritance(self, self.root)

    def _read_num(self):
        numstr = self.root.attrib.get('Num', None):
        if numstr is None:
            return Decimal(0)
        try:
            return LawElementNumber(numstr)
        except LawElementNumberError as e:
            raise LawElementNumberError(self.lawdata, **e.__dict__)

    def _read_text(self):
        return get_text(self.root, "")

class Law(XMLExpansion, LawBase):
    pass

class MainProvision(ProvBase, ETreeLawElementBase):
    pass

class SupplProvision(ProvBase, ETreeLawElementBase):
    pass

class Part(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision,)

class Chapter(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, Part)

class Section(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Chapter,)

class Subsection(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Section,)

class Division(SuperordinateElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Subsection,)

class Article(BasicElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, SupplProvision, Part, Chapter, Section, Subsection, Division)

class ETreeSentenceBase(SentenceBase, ETreeLawElementBase):
    def inheritance(self, root):
        self.root = root
        super().inheritance()

    def extract_text(self):
        return list(get_text(s, "") for s in self.root.findall('./Sentence'.format(self.__class__.__name__)))

class ArticleCaption(CaptionBase, ETreeSentenceBase):
    PARENT_CANDIDATES = (Article,)
    def extract_text(self):
        return [get_text(self.root, '')]

class Paragraph(BasicElementBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (MainProvision, SupplProvision, Article)

class ParagraphSentence(ETreeSentenceBase):
    PARENT_CANDIDATES = (Paragraph,)

class Item(ItemBase, ETreeLawElementBase):
    PARENT_CANDIDATES = (Article, Paragraph)

class ItemSentence(ETreeSentenceBase):
    PARENT_CANDIDATES = (Item,)

class Subitem1(Item):
    PARENT_CANDIDATES = (Item,)

class Subitem1Sentence(ItemSentence):
    PARENT_CANDIDATES = (Item,)

class Subitem2(Item):
    PARENT_CANDIDATES = (Subitem1,)

class Subitem2Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem1,)

class Subitem3(Item):
    PARENT_CANDIDATES = (Subitem2,)

class Subitem3Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem2,)

class Subitem4(Item):
    PARENT_CANDIDATES = (Subitem3,)

class Subitem4Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem3,)

class Subitem5(Item):
    PARENT_CANDIDATES = (Subitem4,)

class Subitem5Sentence(ItemSentence):
    PARENT_CANDIDATES = (Subitem4,)