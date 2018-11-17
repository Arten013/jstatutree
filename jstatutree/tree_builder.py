import unicodedata
import re
from .exceptions import *
from xml.etree import ElementTree as ET
from . import etypes
from .lawdata import LawData, ElementNumber
import os

class JstatutreeBuilder(ET.TreeBuilder):
    SKIP_ELEM_PATTERNS = {
                'sentences': re.compile('(Paragraph|Item|Subitem\d?)Sentence'),
                'captions': re.compile('(Article|Paragraph)Caption'),
                'provisions': re.compile('(Main|Supple)Provision'),
            }
    def __init__(self, lawdata, skip_categories=[etypes.CATEGORY_CAPTION, etypes.CATEGORY_PROVISION], skip_elems=['captions', 'provisions'], root_tag='Law'):
        self._data = [] # data collector
        self._elem = [] # element stack
        self._last = None # last element
        self._root = None
        self._tail = None # true if we're after an end tag
        self._is_main_provision = False
        self.lawdata = lawdata
        self._factory = etypes.element_factory
        #self._skip_elems = [re.compile('UNK')]+[self.SKIP_ELEM_PATTERNS[ptn_name] for ptn_name in skip_elems]
        self._skip_categories = set(skip_categories)
        self._root_tag = root_tag
        self._is_unk_branch_count = 0
        self._codes = []

    def close(self):
        """Flush builder buffers and return toplevel document Element."""
        assert len(self._elem) == 0, "missing end tags"
        assert self._root is not None, "missing toplevel element"
        return self._root

    def _flush(self):
        if self._data:
            if self._last is not None:
                text = "".join(self._data)
                if self._tail:
                    assert self._last.tail is None, "internal error (tail)"
                    self._last.tail = text or ''
                else:
                    assert self._last.text is None, "internal error (text)"
                    self._last.text = text or ''
            self._data = []

    def preprocess(self, data):
        """読み込むデータの前処理"""
        data = unicodedata.normalize("NFKC", data).strip()
        return data

    def data(self, data):
        """読み込んだテキストを前処理を施して追加"""
        data = self.preprocess(data)
        self._data.append(data)

    def _assert_is_appendable(self, subelement):
        if not isinstance(self._elem[-1][0], subelement.__class__.PARENT_CANDIDATES):
            raise HieralchyError(
                self.lawdata,
                "invalid hieralchy: "+ self._elem[-1][0].etype + " -> " + subelement.etype
            )

    def start(self, tag, attrs):
        """
        XMLタグを読み込んだ時に呼び出される。
        *tag* タグ（=要素名）
        *attr* 要素
        """
        self._flush()
        self._last = elem = self._factory(tag, tag, attrs)
        # print(self._last.tag, self._last.etype)
        if tag == 'MainProvision':
            self._is_main_provision = True
        if not self._is_main_provision and not tag == self._root_tag:
            # print('> prov skip')
            self._elem.append([elem, False])
            self._tail = 0
            return elem
        """
        for i, ptn in enumerate(self._skip_elems):
            if ptn.match(elem.etype):
                # print('> elem skip (UNK or skip setting)')
                self._elem.append([elem, False])
                if i == 0:
                    # print('UNK count:',self._is_unk_branch_count,'->',self._is_unk_branch_count+1)
                    self._is_unk_branch_count += 1
                break
        """
        if elem.CATEGORY == etypes.CATEGORY_UNKNOWN:
            # print('UNK count:',self._is_unk_branch_count,'->',self._is_unk_branch_count+1)
            self._is_unk_branch_count += 1
            self._elem.append([elem, False])
        elif elem.CATEGORY in self._skip_categories:
            # print('> elem skip (UNK or skip setting)')
            self._elem.append([elem, False])
        else:
            for e, used in self._elem[::-1]:
                if not used:
                    continue
                if self._is_unk_branch_count == 0:
                    # print('> add {} -> {}'.format(str(e), str(elem)))
                    self._assert_is_appendable(elem)
                    e.append(elem)
                    self._elem.append([elem, True])
                else:
                    # print('> elem skip (under UNK skipper)', self._is_unk_branch_count)
                    self._elem.append([elem, False])
                break
            else:
                if tag == self._root_tag:
                    self._elem.append([elem, True])
                    self._root = elem
                    #print('> add as root')
                else:
                    raise Exception('No root element in the element stack.')
        self._tail = 0
        elem.code = os.path.join(str(self.lawdata.code), *[str(x)  for x, used in self._elem if used])
        #print(self._codes)
        if self._elem[-1][1]:
            if elem.code in self._codes:
                if 'Num' in elem.attrib:
                    raise XMLStructureError(law=self.lawdata, error_detail="Element Code Duplication "+elem.code)
                while elem.code in self._codes:
                    elem.num = ElementNumber(int(elem.num)+1)
                    elem.code = os.path.join(str(self.lawdata.code), *[str(x)  for x, used in self._elem if used])
            self._codes.append(elem.code)
        return elem

    def end(self, tag):
        """
        終了タグを読み込んだ時に呼び出される。
        *tag* タグ（=要素名）
        """
        self._flush()
        self._last, used = self._elem.pop()
        assert self._last.tag == tag,\
               "end tag mismatch (expected %s, got %s)" % (
                   self._last.tag, tag)
        #print('END etype:', self._last.etype)
        if self._is_main_provision and self._last.CATEGORY == etypes.CATEGORY_UNKNOWN:
            self._is_unk_branch_count -= 1
        if self._last.tag == 'MainProvision':
            self._is_main_provision = False
        elif self._last.tag == 'LawNum':
            self.lawdata.lawnum = self._last.text
        elif self._last.tag == 'LawTitle':
            self.lawdata.title = self._last.text
        elif self._last.CATEGORY==etypes.CATEGORY_CAPTION:#'Caption' in self._last.tag:
            self._elem[-1][0].caption = self._last.text
        elif 'Title' in self._last.tag:
            self._elem[-1][0].title = self._last.text
        self._tail = 1
        return self._last
