import re
from xml.etree import ElementTree as ET, ElementPath

from .exceptions import *
from . import etypes
from .lawdata import LawData, ElementNumber
from decimal import Decimal
from pathlib import Path
from . import graph

class Element(ET.Element):
    __slots__ = [
        "attrib",
        "tag",
        "text",
        "tail",
        "_children",
        "code",
        "title",
        "caption",
        "num"
    ]
    
    LEVEL = 0
    SUBLEVEL = 0
    PARENT_CANDIDATES = ()
    JNAME = ""

    def __init__(self, tag, attrib={}, **extra):
        if not isinstance(attrib, dict):
            raise TypeError("attrib must be dict, not %s" % (
                attrib.__class__.__name__,))
        attrib = attrib.copy()
        attrib.update(extra)
        self.attrib = attrib
        self.code = None
        self.tag = tag
        self.text = None
        self.tail = None
        self._children = []
        self.title = ''
        self.caption = ''
        self.num = ElementNumber(self.attrib.get('Num', 1))
        
    def __getstate__(self):
        return (
            self.attrib,
            self.tag,
            self.text,
            self.tail,
            [e for e in self._children],
            self.code,
            self.title,
            self.caption,
            self.num
        )
    
    def __setstate__(self, state):
        for i, attr_name in enumerate(self.__slots__):
            setattr(self, attr_name, state[i])

    def __repr__(self):
        return "<%s %r at %#x>" % (self.__class__.__name__, self.tag, id(self))

    def makeelement(self, tag, attrib):
        return etypes.element_factory(tag, tag, attrib)

    def copy(self):
        elem = self.makeelement(self.tag, self.attrib)
        elem.text = self.text
        elem.tail = self.tail
        elem.title = self.title,
        elem.code = self.code
        elem.caption = self.caption
        elem.num = self.num
        elem[:] = self
        return elem

    def __iter__(self):
        return (e for e in self._children)

    def __len__(self):
        return len(self._children)

    def __getitem__(self, index):
        return self._children[index]

    def __setitem__(self, index, element):
        if isinstance(index, slice):
            for elt in element:
                self._assert_is_element(elt)
        else:
            self._assert_is_element(element)
        self._children[index] = element

    def __delitem__(self, index):
        del self._children[index]

    def append(self, subelement):
        self._assert_is_element(subelement)
        self._children.append(subelement)

    def extend(self, elements):
        for element in elements:
            self._assert_is_element(element)
        self._children.extend(elements)

    def insert(self, index, subelement):
        self._assert_is_element(subelement)
        self._children.insert(index, subelement)

    def _assert_is_element(self, e):
        if not isinstance(e, Element):
            raise TypeError('expected an Element, not %s' % type(e).__name__)

    def remove(self, subelement):
        self._children.remove(subelement)

    def iterfind_by_code(self, code):
        #print(self.code, code, self.code==code)
        if self.code == code:
            yield self
        elif self.code in code:
            #print([c.code for c in self])
            for c in self:
                yield from c.iterfind_by_code(code)
        return
    
    def findall_by_code(self, code):
        return list(self.iterfind_by_code(code))
    
    def find_by_code(self, code):
        for e in self.iterfind_by_code(code):
            return e
        
    def find(self, path, namespaces=None):
        raise Exception()
        return ElementPath.find(self, path, namespaces)

    def findtext(self, path, default=None, namespaces=None):
        raise Exception()
        return ElementPath.findtext(self, path, default, namespaces)

    def findall(self, path, namespaces=None):
        raise Exception()
        return ElementPath.findall(self, path, namespaces)

    def iterfind(self, path, namespaces=None):
        raise Exception()
        return ElementPath.iterfind(self, path, namespaces)

    def clear(self):
        self.attrib.clear()
        self._children = []
        self.text = self.tail = None

    def get(self, key, default=None):
        return self.attrib.get(key, default)

    def set(self, key, value):
        self.attrib[key] = value

    def keys(self):
        return self.attrib.keys()

    def items(self):
        return self.attrib.items()

    def itertext(self):
        tag = self.tag
        if not isinstance(tag, str) and tag is not None:
            return
        t = self.text
        if t:
            yield t
        for e in self:
            yield from e.itertext()
            t = e.tail
            if t:
                yield t

    def iter(self, tag=None):
        if tag == "*":
            tag = None
        if tag is None or self.tag == tag:
            yield self
        for e in self._children:
            #print(e.etype)
            yield from e.iter(tag)

    def is_deleted(self):
        return ''.join(self.itertext()) == '削除'

    @property
    def sentence(self):
        return self.text if self.etype == 'Sentence' else ''

    def itersentence(self, include_code=False, include_value=True):
        if self.etype == 'Sentence':
            yield (self.code, self.sentence) if include_code else self.sentence
        else:
            for child in self.iter('Sentence'):
                yield (child.code, child.sentence) if include_code else child.sentence
        return
    def iterXsentence_code(self):
        yield from self.iterXsentence_elem(include_code=True, include_value=False)

    def iterXsentence_elem(self, include_code=False, include_value=True):
        if self.CATEGORY == etypes.CATEGORY_TEXT:
            if not include_value:
                yield self.code if include_code else None
            else:
                yield (self.code, self) if include_code else self
        else:
            for child in list(self):
                yield from child.iterXsentence_elem(include_code=include_code, include_value=include_value)
            
    def iterXsentence(self, include_code=False, include_value=True):
        if not include_value:
            yield from self.iterXsentence_elem(include_code=include_code, include_value=False)
            return
        for e in self.iterXsentence_elem(False, True):
            item = None
            for s in e.itersentence():
                if item:
                    item += s
                else:
                    item = s
            yield (e.code, item) if include_code else item
            
    @property
    def etype(self):
        return self.__class__.__name__
    
    def __str__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.num.num)

    def to_dot(self, lawname='', *args, **kwargs):
        return graph.element2viz(self, lawname, *args, **kwargs)
    