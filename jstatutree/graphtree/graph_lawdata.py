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
import multiprocessing
import traceback
def find_all_files(directory, extentions=None):
    for root, dirs, files in os.walk(directory):
        if extentions is None or os.path.splitext(root)[1] in extentions:
            yield root
        for file in files:
            if extentions is None or os.path.splitext(file)[1] in extentions:
                yield os.path.join(root, file)
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
from time import sleep
class JStatutreeGDB(object):
    def __init__(self, *args, **kwargs):
        exc = None
        for i in range(50):
            try:
                self.db = GraphDatabase(*args, **kwargs)
                print('connected (retried {} times)'.format(i))
            except Exception as e:
                exc = e
                sleep(0.01)
                continue
            break
        else:
            raise exc

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
                # print('executed', query)
            except Exception as exc:
                # print('skip', query)
                # print(exc)
                pass



    def reg_governments(self, code):
        if int(code) >= 10000:
            code_str = '{0:06}'.format(int(code))
            if code_str in self.governments:
                return
            query = """
                merge (m:Municipalities{code: '%s'})
                merge (p:Prefectures{code: left(m.code, 2)})
                merge (p)-[:PREF_OF]->(m)
                return m, p
            """ % code_str
            mnode, pnode = self.db.query(query, returns=[Node, Node])[0]
            self.governments[mnode['code']] = mnode
            self.governments[pnode['code']] = pnode
            print('reg gov:', mnode['code'])
        else:
            code_str = '{0:02}'.format(int(code))
            if code_str in self.governments:
                print('skip reg gov: ', code_str)
                return
            if code_str in self.governments:
                return
            query = """
                MERGE (p:Prefectures{code: '%s'}
                RETURN p
            """ % code_str
            pnode = self.db.query(query)[0]
            self.governments[pnode['code']] = pnode
            print('reg gov:', pnode['code'])

    def reg_lawdata(self, lawdata):
        self.reg_governments(lawdata.municipality_code)
        query = """
            MATCH (m:Municipalities{code: '%s'})
            MERGE (s:Statutories{code: '%s', name: '%s', lawnum: '%s'})
            ON CREATE SET s.created='true'
            ON MATCH SET s.created='false'
            MERGE (m)-[:MUNI_OF]->(s)
            WITH s, s.created AS created
            REMOVE s.created
            RETURN s, created
        """ % (lawdata.municipality_code, lawdata.file_code, lawdata.name, lawdata.lawnum)
        res = self.db.query(query, returns=[Node, bool])
        return res[0][0] if res[0][1] else None

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

def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
            for i in range(wanted_parts) ]

import concurrent
import configparser

class DBConfig(object):
    def __init__(self, path=None):
        self.parser = configparser.ConfigParser()
        if path is not None:
            self.path = path
            os.path.exists(self.path) and self.load()
        self.section = self.parser['DEFAULT']

    def change_section(self, name, create_if_missing=True):
        if create_if_missing:
            self.parser.add_section(name)
        assert self.parser.has_section(name), 'There is no section named '+name+'.'
        self.section = self.parser[name]

    def set_path(self, path):
        self.path = path

    def load(self):
        with open(self.path) as f:
            self.parser.read_file(f)

    def save(self):
        os.makedirs(os.path.split(self.path)[0], exist_ok=True)
        with open(self.path, 'w') as f:
            self.parser.write(f, self)

    def update(self):
        assert self.path is not None, 'You must set path before reload database configure'
        self.save()
        self.load()

    def set_logininfo(self, host='localhost', port='17474', usr='neo4j', pw='pass'):
        self.section.update(
                {
                    'port': str(port),
                    'usr': usr,
                    'pw': pw,
                    'host': host,
                }
            )

    @property
    def url(self):
        return 'http://{host}:{port}'.format(host=self.section['host'], port=self.section['port'])

    @property
    def loginkey(self):
        return {
                    'username': self.section['usr'],
                    'password': self.section['pw'],
                    'url': self.url
                }

def register_directory(loginkey, levels, basepath, only_reiki=True, only_sentence=True, workers=multiprocessing.cpu_count()):
    path_lists = split_list(list(find_all_files(basepath, [".xml"])), workers)
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as proc_exec:
        futures = [
                proc_exec.submit(
                        register_from_pathlist,
                        pathlist=path_lists[i],
                        loginkey=loginkey,
                        levels=levels,
                        only_reiki=only_reiki,
                        only_sentence=only_sentence
                    ) for i in range(workers)
                ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception:
                traceback.print_exc()
from jstatutree.xmltree import xml_lawdata
def register_from_pathlist(pathlist, loginkey, levels, only_reiki, only_sentence):
    gdb = ReikiGDB(**loginkey)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(
            set_data_from_reader,
            gdb=gdb,
            reader=xml_lawdata.ReikiXMLReader(path),
            only_reiki=only_reiki,
            only_sentence=only_sentence,
            levels=levels
            ) for path in pathlist]
        for future in concurrent.futures.as_completed(futures):
            try:
                print(future.result())
            except Exception:
                traceback.print_exc()

def set_data_from_reader(gdb, reader, levels, only_reiki, only_sentence):
    if gdb.load_lawdata(reader.lawdata.municipality_code, reader.lawdata.file_code) is not None:
        return 'skip(exists): '+str(reader.lawdata.name)
    reader.open()
    if reader.is_closed():
        return 'skip(cannot open): '+str(reader.lawdata.name)
    elif not only_reiki or reader.lawdata.is_reiki():
        gdb.set_from_reader(reader, levels=levels)
        ret = 'register: '+str(reader.lawdata.name)
    else:
        ret = 'skip(not reiki): '+str(reader.lawdata.name)
    reader.close()
    return ret
