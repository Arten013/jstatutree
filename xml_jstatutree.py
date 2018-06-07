from jstatutree import SourceInterface, get_etypes, ReikiData, LawData
import xml_etypes as etype
import os
import unicodedata
import re

import xml.etree.ElementTree as ET

def get_text(b, e_val):
    if b is not None and b.text is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

ETYPES = get_etypes(etype)

class XMLReaderBase(SourceInterface):
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.file = None

    @property
    def lawdata(self):
        if "_lawdata" not in self.__dict__ or self._lawdata is None:
            if self.is_closed():
                self.open()
                self._lawdata = self.read_lawdata()
                self.close()
            else:
                self._lawdata = self.read_lawdata()
        return self._lawdata     

    def open(self):
        with open(self.path) as f:
            s = f.read()
        try:
            self.root_etree = ET.fromstring(s)
        except Exception as e:
            print(e)
            print("Parse error")

    def close(self):
        self.root_etree = None

    def is_closed(self):
        return self.root_etree is None

    def get_tree(self):
        root = ETYPES[0](self.lawdata)
        root.root = self.root_etree.find("./Law")
        return root

    def _read_law_name(self):
        return get_text(self.root_etree.find('Law/LawBody/LawTitle'), None)

    def _read_lawnum(self):
        lawnum_text = get_text(self.root_etree.find('Law/LawNum'), "")
        lawnum_text = unicodedata.normalize("NFKC", lawnum_text)
        return None if len(lawnum_text) == 0 else lawnum_text

    def read_lawdata(self):
        lawdata =LawData()
        lawdata.name = self._read_law_name()
        lawdata.lawnum = self._read_lawnum()

        return lawdata

class ReikiXMLReader(XMLReaderBase):
    def read_lawdata(self):
        lawdata =ReikiData()
        # reikicodeの設定
        p, file = os.path.split(self.path)
        lawdata.file_code = os.path.splitext(file)[0]
        p, lawdata.municipality_code = os.path.split(p)
        _, lawdata.prefecture_code = os.path.split(p)

        lawdata.name = self._read_law_name()
        lawdata.lawnum = self._read_lawnum()

        return lawdata
