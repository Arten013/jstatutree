import re
from xml.etree import ElementTree as ET, ElementPath

from .exceptions import *
from . import etypes
from .lawdata import LawData, ElementNumber
from decimal import Decimal

class Element(ET.Element):
    LEVEL = 0
    SUBLEVEL = 0
    PARENT_CANDIDATES = ()
    JNAME = ""

    tag = None
    attrib = None
    text = None
    tail = None

    def __init__(self, tag, attrib={}, **extra):
        if not isinstance(attrib, dict):
            raise TypeError("attrib must be dict, not %s" % (
                attrib.__class__.__name__,))
        attrib = attrib.copy()
        attrib.update(extra)
        self.tag = tag
        self.attrib = attrib
        self._children = []
        self.title = ''
        self.caption = ''
        self._num = None

    def __repr__(self):
        return "<%s %r at %#x>" % (self.__class__.__name__, self.tag, id(self))

    def makeelement(self, tag, attrib):
        return etypes.element_factory(tag, tag, attrib)

    def copy(self):
        elem = self.makeelement(self.tag, self.attrib)
        elem.text = self.text
        elem.tail = self.tail
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

    def find(self, path, namespaces=None):
        return ElementPath.find(self, path, namespaces)

    def findtext(self, path, default=None, namespaces=None):
        return ElementPath.findtext(self, path, default, namespaces)

    def findall(self, path, namespaces=None):
        return ElementPath.findall(self, path, namespaces)

    def iterfind(self, path, namespaces=None):
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
        return self.text if self.etype(True) == 'Sentence' else ''

    def itersentence(self):
        if self.etype == 'Sentence':
            yield self.sentence
        else:
            for child in self.iter('Sentence'):
                yield child.sentence
        raise StopIteration()

    @property
    def etype(self):
        return self.__class__.__name__

    @property
    def num(self):
        if 'Num' in self.attrib:
            self._num = ElementNumber(self.attrib['Num'])
        return self._num or ElementNumber(Decimal(1))

    # "X法第n条第m項"のように出力
    def __str__(self):
        return '{0}({1})'.format(self.__class__.__name__, self.num.num)
