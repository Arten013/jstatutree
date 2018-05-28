
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

class Law(XMLExpansion, jstatutree.Law):
    pass

class LawBody(XMLExpansion, jstatutree.LawBody):
    pass

class MainProvision(XMLExpansion, jstatutree.MainProvision):
    pass

class Part(XMLExpansion, jstatutree.Part):
    pass

class Chapter(XMLExpansion, jstatutree.Chapter):
    pass

class Section(XMLExpansion, jstatutree.Section):
    pass

class Subsection(XMLExpansion, jstatutree.Subsection):
    pass

class Division(XMLExpansion, jstatutree.Division):
    pass

class Article(XMLExpansion, jstatutree.Article):
    pass

class ArticleCaption(XMLExpansion, jstatutree.ArticleCaption):
    pass

class Paragraph(XMLExpansion, jstatutree.Paragraph):
    pass

class ParagraphSentence(XMLExpansion, jstatutree.ParagraphSentence):
    pass

class ParagraphCaption(XMLExpansion, jstatutree.ParagraphCaption):
    pass

class Item(XMLExpansion, jstatutree.Item):
    pass

class ItemSentence(XMLExpansion, jstatutree.ItemSentence):
    pass

class Subitem1(XMLExpansion, jstatutree.Subitem1):
    pass

class Subitem1Sentence(XMLExpansion, jstatutree.Subitem1Sentence):
    pass

class Subitem2(XMLExpansion, jstatutree.Subitem2):
    pass

class Subitem2Sentence(XMLExpansion, jstatutree.Subitem2Sentence):
    pass

class Subitem3(XMLExpansion, jstatutree.Subitem3):
    pass

class Subitem3Sentence(XMLExpansion, jstatutree.Subitem3Sentence):
    pass

class Subitem4(XMLExpansion, jstatutree.Subitem4):
    pass

class Subitem4Sentence(XMLExpansion, jstatutree.Subitem4Sentence):
    pass

class Subitem5(XMLExpansion, jstatutree.Subitem5):
    pass

class Subitem5Sentence(XMLExpansion, jstatutree.Subitem5Sentence):
    pass

class Sentence(XMLExpansion, jstatutree.Sentence):
    pass
