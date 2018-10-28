from . import etypes
from . import element
from . import tree_builder
from . import lawdata
from . import exceptions

import unicodedata
import re
from xml.etree import ElementTree as ET

class Jstatutree(ET.ElementTree):
    def __init__(self, path):
        self.lawdata = lawdata.LawData(path=path)
        parser = ET.XMLParser(target=tree_builder.JstatutreeBuilder(lawdata=self.lawdata))
        with open(path, "rb") as source:
            while True:
                data = source.read(65536)
                if not data:
                    break
                parser.feed(data)
            self._root = parser.close()
