from jstatutree import SourceInterface

def get_text(b, e_val):
    if b is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

class ReikiXMLReader(SourceInterface):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.file = None

    def open(self):
        self.root_etree = ET.parse(self.path).getroot()

    def close(self):
        self.root_etree = None

    def get_tree(self, tree_base):
        root = Law(tree_base)
        root.inheritance(self.root_etree)
        root.lawdata = self.get_lawdata()
        return root

    def get_lawdata(self):
        lawdata = ReikiData()

        # reikicodeの設定
        p, file = os.path.split(self.path)
        lawdata.file_code = os.path.splitext(file)[0]
        p, lawdata.municipality_code = os.path.split(p)
        _, lawdata.prefecture_code = os.path.split(p)

        # nameの設定
        lawdata.name = get_text(self.root_etree.find('Law/LawBody/LawTitle'), None)

        # lawnumの設定
        lawnum_text = get_text(self.root_etree.find('Law/LawNum'), "")
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
