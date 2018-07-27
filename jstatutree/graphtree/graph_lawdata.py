import sys, os
import os
import unicodedata
import re
import inspect
import xml.etree.ElementTree as ET
from jstatutree.lawdata import SourceInterface, ReikiData, LawData
from . import graph_etypes
from neo4jrestclient.client import GraphDatabase, Node
import neo4jrestclient
from time import sleep

def get_text(b, e_val):
    if b is not None and b.text is not None and len(b.text) > 0:
        return b.text
    else:
        return e_val

ETYPES = graph_etypes.get_etypes()

class GDBReikiData(ReikiData):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self._code = "00/000000/0000"
        self._id = 0

    @property
    def prefecture_code(self):
        return self.node['prefecture_code']

    @property
    def municipality_code(self):
        return self.node['municipality_code']

    @property
    def file_code(self):
        return self.node['file_code']

class JStatutreeGDB(object):
    def __init__(self, usr, pw, url="http://localhost:7474/db/data"):
        self.usr = usr
        self.pw = pw
        self.url = url
        self.db = GraphDatabase(url, username=usr, password=pw)

    def get_properties(self, node_id):
        return self.db.node[node_id].properties

    def find_children(self, node_id):
        parent_node = self.db.node[node_id].Child
        for rel in parent_node.relationships.outgoing(['Children']):
            yield rel.end

    def reg_lawdata(self, lawdata):
        return self.db.nodes.create(code=lawdata.code, name=lawdata.name, lawnum=lawdata.lawnum)

    def reg_element(self, elem, label='Elements'):
        node = self.db.nodes.create(
                name=elem.name if elem.name!='' else elem.etype.__name__,
                fullname=str(elem),
                num=str(elem.num.num),
                text=elem.text,
                fulltext=''.join(elem.iter_sentences()),
                etype=elem.etype.__name__
                )
        node.labels.add(label)
        return node

    def reg_tree(self, tree, tree_node=None):
        tree_node = self.reg_element(tree) if tree_node is None else tree_node
        for child_elem in tree.children.values():
            child_node = self.reg_element(child_elem)
            tree_node.relationships.create('HAS_ELEM', child_node)
            self.reg_tree(child_elem, child_node)
        return tree_node

    def reg_level_restricted_tree(self, tree, levels, tree_node=None, level_index=0):
        if level_index >= len(levels):
            return
        tree_node = self.reg_element(tree, label=tree.etype.__name__+'s') if tree_node is None else tree_node
        for child_elem in tree.depth_first_search(levels[level_index], valid_vnode=True):
            if tree.etype == child_elem.etype:
                self.reg_level_restricted_tree(tree, levels, tree_node, level_index+1)
                break
            else:
                child_node = self.reg_element(child_elem, label=child_elem.etype.__name__+'s')
                tree_node.relationships.create('HAS_ELEM', child_node)
                self.reg_level_restricted_tree(child_elem, levels, child_node, level_index+1)
        return tree_node

    def set_from_reader(self, reader, levels='ALL'):
        lawdata_node = self.reg_lawdata(reader.lawdata)
        if levels == 'ALL':
            tree_node = self.reg_tree(reader.get_tree())
        else:
            tree_node = self.reg_level_restricted_tree(reader.get_tree(), levels)
        lawdata_node.relationships.create('TREE', tree_node)
        return lawdata_node

class ReikiGDB(JStatutreeGDB):
    INDEX_TYPE = {
            'Prefectures': {
                'attrs': 'code',
                'constraint': "UNIQUE"
                },
            'Municipalities': {
                'attrs': 'code',
                'constraint': "UNIQUE"
                },
            'Statutories': {
                'attrs': ['code', 'lawnum', 'name'],
                'constraint': None
                }
            }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_db()
        self.governments = self.load_govs()

    def init_db(self):
        query = ''
        for name, config in self.INDEX_TYPE.items():
            if config['constraint'] == 'UNIQUE':
                query = 'CREATE CONSTRAINT ON (n:{name}) ASSERT n.{attr} IS UNIQUE;'.format(
                        name=name,
                        attr=config['attrs']
                        )
            elif config['constraint'] == 'NODE KEY':
                query = 'CREATE CONSTRAINT ON (n:{name}) ASSERT ({attrs}) IS NODE KEY;'.format(
                        name=name,
                        attrs=", ".join(map(lambda x: "n."+x, config['attrs']))
                        )
            else:
                query = 'CREATE INDEX ON :{name}({attrs});\n'.format(
                    name=name,
                    attrs=", ".join(config['attrs'])
                        )
            try:
                self.db.query(query)
                print('executed', query)
            except Exception as exc:
                print('skip', query)
                print(exc)


    def reg_lawdata(self, lawdata):
        if lawdata.prefecture_code not in self.governments:
            node = self.db.nodes.create(code=lawdata.prefecture_code)
            node.labels.add('Prefectures')
            self.governments[lawdata.prefecture_code] = node
        if lawdata.municipality_code not in self.governments:
            node = self.db.nodes.create(code=lawdata.municipality_code)
            node.labels.add('Municipalities')
            self.governments[lawdata.municipality_code] = node
            self.governments[lawdata.prefecture_code].relationships.create('PREF_OF', node)
        node = self.db.nodes.create(code=lawdata.file_code, name=lawdata.name, lawnum=lawdata.lawnum)
        node.labels.add('Statutories')
        self.governments[lawdata.municipality_code].relationships.create('MUNI_OF', node)
        return node

    def load_lawdata(self, muni_code, file_code):
        query = """
            MATCH (muni:Municipalities)
                  -[:MUNI_OF]->(stat:Statutories)
            WHERE muni.code='{mc:06}' AND stat.code='{sc:04}'
            RETURN stat
                """.format(mc=int(muni_code), sc=int(file_code))
        node = self.db.query(query)
        return GDBReikiData(node[0]) if len(node)==1 else None

    #def link_govs(self):
    #    query = """
    #        MATCH (pref:Prefectures), (muni:Municipalities)
    #        WHERE NOT pref-[:PREF_OF]->muni
    #        AND pref.code*10000 < muni.code AND (pref.code+1)*10000 > muni.code
    #        CREATE (pref)-[:PREF_OF]->(muni)
    #    """
    #    self.db.query(query)

    def load_govs(self):
        query = """
            MATCH (pref:Prefectures)
            RETURN pref.code AS gcode, pref AS gnode
            UNION ALL MATCH (muni:Municipalities)
            RETURN muni.code AS gcode, muni AS gnode;
            """
        govs = {}
        for gcode, gnode in self.db.query(query, returns=[str, Node]):
            govs[gcode] = gnode
        return govs

class GDBReaderBase(SourceInterface):
    def __init__(self, code, db):
        self.code = code
        self.db = db

    def get_tree(self):
        return ETYPES[0](self.lawdata)

    def read_lawdata(self):
        return self.db.load_lawdata(self.code)

    def is_closed(self):
        return False

class ReikiGDBReader(GDBReaderBase):
    pass
