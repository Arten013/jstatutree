from . import etypes
from . import element
from . import tree_builder
from . import lawdata
from . import exceptions
from . import graph

from xml.etree import ElementTree as ET
import copy

class Jstatutree(ET.ElementTree):
    def __init__(self, path):
        self.lawdata = lawdata.LawData(path=path)
        self._find_cache = {}
        parser = ET.XMLParser(target=tree_builder.JstatutreeBuilder(lawdata=self.lawdata))
        with open(path, "rb") as source:
            while True:
                data = source.read(65536)
                if not data:
                    break
                parser.feed(data)
            self._root = parser.close()

    def __getstate__(self):
        self._find_cache = None
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._find_cache = {}

    def iterXsentence(self, *args, **kwargs):
        yield from self._root.iterXsentence(*args, **kwargs)

    def to_dot(self, *args, **kwargs):
        return graph.element2viz(self.getroot(), self.lawdata.name, *args, *kwargs)
    
    def iterfind_by_code(self, code):
        yield from self.getroot().iterfind_by_code(code)

    def find_by_code(self, code):
        ret = self._find_cache.get(code, None)
        if ret is None:
            ret = self.getroot().find_by_code(code)
            self._find_cache[code] = ret
        return ret
    
    def findall_by_code(self, code):
        return self.getroot().findall_by_code(code)
    
    def iterXsentence_code(self):
        yield from self.iterXsentence(include_code=True, include_value=False)

    def iterXsentence_elem(self, include_code=False, include_value=True):
        yield from self.getroot().iterXsentence_elem(include_code=include_code, include_value=include_value)

    def change_root(self, code):
        if str(code) == str(self.lawdata.code):
            return self
        tree = copy.copy(self)
        tree._find_cache = {}
        new_root = tree.find_by_code(code)
        if new_root is None:
            raise KeyError(code)
        tree._root = new_root
        tree.lawdata.code = tree.lawdata.code.__class__(code)
        return tree

