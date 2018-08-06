import sys, os
import os
import unicodedata
import re
import inspect
from jstatutree.xmltree import xml_lawdata, xml_etypes
from jstatutree.lawdata import SourceInterface, ReikiData, LawData
from jstatutree.myexceptions import LawError
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
                sleep(0.1)
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
def register_from_pathlist(pathlist, loginkey, levels, only_reiki, only_sentence):
    gdb = ReikiGDB(**loginkey)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for path in pathlist: 
            reader=xml_lawdata.ReikiXMLReader(path)
            if gdb.load_lawdata(reader.lawdata.municipality_code, reader.lawdata.file_code) is not None:
                 print('skip(exists): '+str(reader.lawdata.name))
                 continue
            reader.open()
            if reader.is_closed():
                print('skip(cannot open): '+str(reader.lawdata.name))
                continue
            if only_reiki and not reader.lawdata.is_reiki():
                print('skip(not reiki): '+str(reader.lawdata.name))
                reader.close()
                continue
            futures.append(
                    executor.submit(
                            set_from_reader,
                            reader=reader,
                            levels=levels
                        )
                )
        for future in concurrent.futures.as_completed(futures):
            result, output, lawdata = future.result()
            if result:
                gdb.reg_lawdata(lawdata)
                gdb.db.query(output)
                print('register: '+str(lawdata.name))
            else:
                print(output)

def set_from_reader(reader, levels='ALL'):
    levels = levels if levels != 'ALL' else xml_etypes.get_etypes()
    try:
        tree = reader.get_tree()
        cypher = """MATCH (:Municipalities{code: '%s'})-[:MUNI_OF]->(stat:Statutories{code: '%s'})\n""" % (reader.lawdata.municipality_code, reader.lawdata.file_code)
        cypher += tree.subtree_cypher(levels)
        cypher += """,\n\t(stat)-[:TREE]->(%s)""" % (tree.cypher_node_name)
        ret = True, cypher, reader.lawdata
    except LawError as e:
        ret = False, str(e), None
    except Exception as e:
        ret = False, traceback.format_exc(), None
    finally:
        reader.close()
        return ret
