from . import etypes
from . import element
from . import tree_builder
from . import lawdata
from . import exceptions
from . import graph

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
            
    def iterXsentence(self, *args, **kwargs):
        yield from self._root.iterXsentence(*args, **kwargs)

    def to_dot(self, *args, **kwargs):
        return graph.element2viz(self.getroot(), self.lawdata.name, *args, *kwargs)
    
    def iterfind_by_code(self, code):
        yield from self.getroot().iterfind_by_code()

    def find_by_code(self, code):
        return self.getroot().find_by_code(code)
    
    def findall_by_code(self, code):
        return self.getroot().findall_by_code(code)