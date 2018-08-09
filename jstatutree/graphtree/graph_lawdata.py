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
    def __init__(self, max_retry=50, *args, **kwargs):
        exc = None
        for i in range(max_retry):
            try:
                # self.db = GraphDatabase(*args, **kwargs)
                self.driver = GraphDatabase.driver("bolt://localhost:7687")
                print('connected (retried {} times)'.format(i))
            except Exception as e:
                exc = e
                sleep(0.1)
                continue
            break
        else:
            print('failed to connect neo4j server(retried {} times)'.format(max_retry))
            raise exc

    # def get_properties(self, node_id):
        # return self.db.node[node_id].properties

    # def find_children(self, node_id):
        # parent_node = self.db.node[node_id].Child
        # for rel in parent_node.relationships.outgoing(['Children']):
            # yield rel.end

    # def reg_lawdata(self, lawdata):
    #     return self.db.nodes.create(code=lawdata.code, name=lawdata.name, lawnum=lawdata.lawnum)


class ReikiGDB(JStatutreeGDB):
    INDEX_TYPE = {
            'Prefectures': {
                'attrs': ['code'],
                'constraint': "UNIQUE"
                },
            'Municipalities': {
                'attrs': ['code'],
                'constraint': "UNIQUE"
                },
            'Statutories': {
                'attrs': ['code'],
                'constraint': 'UNIQUE'
                }
            'Elements': {
                'attrs': ['id'],
                'constraint': 'UNIQUE'
                }
            }
    governments = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with self.driver.session() as session:
            session.write_transaction(self.init_db)
            session.read_transaction(self.load_govs)

    def __del__(self):
        self.close()

    def close(self):
        self.driver.close()

    @classmethod
    def init_db(cls, tx):
        for name, config in cls.INDEX_TYPE.items():
            if config['constraint'] == 'UNIQUE':
                query = 'CREATE CONSTRAINT ON (n:{$name}) ASSERT n.{$attr} IS UNIQUE;'
                kwargs = {'name': name, attr: config['attrs'][0]}
            else:
                query = 'CREATE INDEX ON :{name}({attrs});\n'
                kwargs = {'name': name, attr: ", ".join(config['attrs']}
            try:
                tx.run(query, **kwargs)
            except Exception as exc:
                print('skip', query)
                print(exc)
                pass

    @classmethod
    def load_govs(cls, tx):
        query = """
            MATCH (pref:Prefectures)
            RETURN pref.code AS gcode
            UNION ALL MATCH (muni:Municipalities)
            RETURN muni.code AS gcode;
            """
        self.__class__governments = list(set(
                self.__class__.governments.extend([res['gcode'] for res in tx.run(query)})
            ))

    @classmethod
    def reg_governments(self, tx, code):
        if int(code) >= 10000:
            code_str = '{0:06}'.format(int(code))
            if code_str in self.governments:
                return
            query = """
                merge (m:Municipalities{code: $code})
                merge (p:Prefectures{code: left(m.code, 2)})
                merge (p)-[:PREF_OF]->(m)
                return m.code, p.code
            """
            record = tx.run(query, code=code_str)[0]
            mcode, pcode = record['m.code'], record['p.code']
            mcode not in self.governments and self.__class__.governments.append(mcode)
            pcode not in self.governments and self.__class__.governments.append(pcode)
            print('reg gov:', mcode)
        else:
            code_str = '{0:02}'.format(int(code))
            if code_str in self.governments:
                print('skip reg gov: ', code_str)
                return
            if code_str in self.governments:
                return
            query = """
                MERGE (p:Prefectures{code: $code}
                RETURN p.code
            """
            record = tx.run(query, code=code_str)[0]
            pcode = record['p.code']
            pcode not in self.governments and self.__class__.governments.append(pcode)
            print('reg gov:', pcode)

    def reg_lawdata(self, lawdata):
        with self.driver.session as session
        self.reg_governments(lawdata.municipality_code)
        query = """
            MATCH (m:Municipalities{code: '%s'})
            MERGE (s:Statutories{code: '%s', name: '%s', lawnum: '%s', id:'%s', tree: 'not_exists'})
            ON CREATE SET s.created='true'
            ON MATCH SET s.created='false'
            MERGE (m)-[:MUNI_OF]->(s)
            WITH s, s.created AS created
            REMOVE s.created
            RETURN s.id, created
        """ % (lawdata.municipality_code, lawdata.file_code, lawdata.name, lawdata.lawnum, lawdata.code)
        res = self.db.query(query, returns=[str, bool])
        return res[0][0] if res[0][1] else None
    
    @classmethod
    def clean_broken_tree(cls, tx, node_id=None):
        query = """
                MATCH (n:Statutories{tree: 'not_exists'})%s
                WITH n
                MATCH (n)-[*]->(m)
                DETACH DELETE n
                DETACH DELETE m
            """ % ('' if node_id is None else """\n                WHERE n.id='{}'""".format(node_id))
        tx.run(query)

    @classmethod
    def mark_tree(cls, tx, statutory_node_id):
        tx.run("""
                MATCH (n:Statutories{id: $node_id})
                WITH n
                LIMIT 1
                SET n.tree='exists';
                """, node_id=statutory_node_id)

    def load_lawdata(self, muni_code, file_code):
        query = """
            MATCH (muni:Municipalities)
                  -[:MUNI_OF]->(stat:Statutories)
            WHERE muni.code='{mc:06}' AND stat.code='{sc:04}'
            RETURN stat
                """.format(mc=int(muni_code), sc=int(file_code))
        with self.driver.session() as session:
            result = session.run(query)
        return GDBReikiData(result[0]['stat']) if len(result)==1 else None
    
    def register_reiki(self, lawdata, cypherizer):
        with self.gdb.driver.session() as session:
            lawdata_id = session.write_transaction(self.reg_lawdata, lawdata)
            # print('hoge:', lawdata_id)
            cypher_generator = cypherizer.gen_cyphers(lawdata_id):
            query = next(cypher_generator)
            while query is not None:
                query = cypher_generator.send(session.run(query).single())
            session.write_transaction.(self.mark_tree, lawdata_id)

from queue import Queue
class TreeCypherizer(object):
    def __init__(self, levels, valid_vnode=True, tx_size_limit=20):
        self.levels = levels
        self.valid_vnode = valid_vnode
        self.tx_size_limit = tx_size_limit
        self.queue = Queue()

    def cypher_result_map(self, result):
        return {
                res[3*i]: {
                    'parent_node_label': res[3*i+1]+'s',
                    'parent_node_id': str(res[3*i+2])
                    }
                for i in range(len(res)//3)
                }

    def gen_cyphers(self, lawdata_id):
        node_infos = self.cypher_result_map(yield self.queue.get().query('Statutories', lawdata_id))
        while not self.queue.empty:
            cypher = self.queue.get()
            node_infos.update(yield cypher.query(**node_infos[str(cypher.require_node)])
        yield None

    def cypherize(self, root):
        assert self.queue.empty(), 'You must finish generating previous cyphers before you set another.'
        self.node_num = 0
        cypher = TreeCypher(self, 'lawdata_node')
        nodes = root.depth_first_iteration(self.levels, valid_vnode=self.valid_vnode)
        cypher.add_root(next(nodes))
        for node in nodes:
            if cypher.add_node(node):
                continue
            self.cyphers.put(cypher)
            cypher = TreeCypher(self)
            cypher.add_root(node)
        self.cyphers.put(cypher)

    def get_node_num(self):
        ret = self.node_num
        self.node_num += 1
        return self.node_num

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


DEFAULT_MAX_CHUNK_SIZE = 30
def register_directory(loginkey, levels, basepath, only_reiki=True, only_sentence=True, workers=multiprocessing.cpu_count(), max_chunk_size=DEFAULT_MAX_CHUNK_SIZE):
    def get_future_results(futures, timeout=None):
        cancelled = []
        for future in futures:
            print('proc-future', future.processing_path_list_id, 'finished')
            try:
                future.result(timeout=timeout)
                print('proc-future', future.processing_path_list_id, 'succeed')
            except concurrent.futures.TimeoutError:
                print('proc-future', future.processing_path_list_id, 'timeout and retry')
                cancelled.extend(path_lists[future.processing_path_list_id])
            except concurrent.futures.CancelledError:
                print('proc-future', future.processing_path_list_id, 'canncelled and retry')
                cancelled.extend(path_lists[future.processing_path_list_id])
            except KeyError:
                print('proc-future', future.processing_path_list_id, 'raised and retry')
                cancelled.extend(path_lists[future.processing_path_list_id])
            except Exception:
                print('proc-future', future.processing_path_list_id, 'raised and retry')
                traceback.print_exc()
                cancelled.extend(path_lists[future.processing_path_list_id])
        return cancelled
    remains = None
    while remains is None or len(remains):
        all_path_list = list(find_all_files(basepath, [".xml"])) if remains is None else remains
        remains = []
        path_count = len(all_path_list)
        chunk_size = min(max_chunk_size, max(1, path_count//workers))
        path_lists = [all_path_list[i:min(i+chunk_size, path_count)] for i in range(0, path_count, chunk_size)]
        chunk_count = len(path_lists)
        for j in range(chunk_count//workers):
            print('iter', j)
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as proc_exec:
                futures = []
                for i in range(workers):
                    target_chunk_index = i + j*workers
                    if target_chunk_index >= chunk_count:
                        break
                    future = proc_exec.submit(
                                register_from_pathlist,
                                pathlist=path_lists[target_chunk_index],
                                loginkey=loginkey,
                                levels=levels,
                                only_reiki=only_reiki,
                                only_sentence=only_sentence,
                                user_num=target_chunk_index
                            )
                    future.processing_path_list_id = target_chunk_index
                    futures.append(future)
                    print('proc-future', target_chunk_index, 'submitted')
                waited = concurrent.futures.wait(futures, timeout=chunk_size*2)
                done, not_done = list(waited.done), list(waited.not_done)
                remains.extend(get_future_results(done))
                for future in not_done:
                    if future.done():
                        continue
                    future.cancel()
                remains.extend(get_future_results(not_done))
        # workers=1


from time import sleep
def register_from_pathlist(pathlist, loginkey, levels, only_reiki, only_sentence, user_num):
    # raise 
    loginkey['username'] += str(user_num)
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
                            reader_to_cyphers,
                            reader=reader,
                            levels=levels
                        )
                )
        for future in concurrent.futures.as_completed(futures):
            result, output, lawdata = future.result()
            if result:
                cyphers = output
                complete_flag = False
                exception = None
                for i in range(5):
                    lawdata_id = None
                    try:
                    except Exception as e:
                        sleep(0.1)
                        exception = e
                        traceback.print_exc()
                        gdb.clean_broken_tree(lawdata_id)
                else:
                    raise exception
                print('register: '+str(lawdata.name))
            else:
                print(output)
            gdb.clean_broken_tree()

def reader_to_cyphers(reader, levels='ALL'):
    levels = levels if levels != 'ALL' else xml_etypes.get_etypes()
    try:
        tree = reader.get_tree()
        cypherizer = TreeCypherizer(levels)
        cyphers = list(cypherizer.iter_subtree_cyphers(tree))
        ret = True, cyphers, reader.lawdata
    except LawError as e:
        ret = False, str(e), None
    except Exception as e:
        ret = False, traceback.format_exc(), None
    finally:
        reader.close()
        return ret

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


def cypher_node_name(node):
    return re.sub('[()]', '', re.sub('/', '_', node.code[15:]))

def cypher_node_edge(srcnode, tarnode):
    src_node_name = srcnode if isinstance(srcnode, str) else cypher_node_name(srcnode)
    tar_node_name = tarnode if isinstance(tarnode, str) else cypher_node_name(tarnode)
    return '(%s)-[:HAS_ELEM]->(%s)' % (src_node_name, tar_node_name)




class TreeCypher(object):
    def __init__(self, cypherizer, require_node=None):
        self.cypherizer = cypherizer
        self.tx_size_limit = cypherizer.tx_size_limit
        self.levels = cypherizer.levels #[level if isinstance(level, str) else level.__name__ for level in levels]
        self.nodes = []
        self.edges = []
        self.require_node = require_node

    def __len__(self):
        return len(self.edges) + len(self.nodes)

    def create_cypher(self, node):
        return ''.join([
            """(%s:%s{""" % (cypher_node_name(node), node.etype.__name__ + 's'),
            """name: '%s',""" % (node.name if node.name!='' else node.etype.__name__),
            """fullname: '%s',""" % str(node),
            """num: '%s',""" % str(node.num.num),
            """text: '%s',""" % node.text, #(node.text if len(node.text) < 5 else node.text[:5]),
            """fulltext: '%s',""" % ''.join(node.iter_sentences()),#[:5],
            """etype: '%s',""" % node.etype.__name__,
            """id: '%s'""" % (node.lawdata.code+'/'+str(self.cypherizer.get_node_num())),
            """})"""
            ])

    def add_root(self, node):
        if self.require_node == 'lawdata_node':
            self.nodes.append(node)
            return
        parent_node = node.parent.search_nearest_parent(self.levels, valid_vnode=True)
        assert parent_node is not None, 'Unexpected Error'
        self.require_node = parent_node
        self.edges.append((parent_node, node))
        self.nodes.append(node)
        return True

    def add_node(self, node):
        parent_node = node.parent.search_nearest_parent(self.levels, valid_vnode=True)
        assert parent_node is not None, 'You cannot add root node using add_node()'
        if len(self) + 2 >= self.tx_size_limit:
            return False
        if not parent_node in self.nodes+[self.require_node]:
            return False
        self.edges.append((parent_node, node))
        self.nodes.append(node)
        return True

    @property
    def create_node_lines(self):
        return ',\n\t'.join([self.create_cypher(n) for n in self.nodes])

    @property
    def create_edge_lines(self):
        l = []
        for n1, n2 in self.edges:
            if not isinstance(self.require_node, str) and n1 == self.require_node:
                l.append(cypher_node_edge('pn', n2))
            else:
                l.append(cypher_node_edge(n1, n2))
        return ',\n\t'.join(l)

    @property
    def return_lines(self):
        return ',\n\t'.join([
                "{node_name}.fullname, {node_name}.etype, {node_name}.id".format(
                        node_name=cypher_node_name(n),
                    )
                for n in self.nodes])

    def query(self, parent_node_label, parent_node_id):
        ret = {
            'q': """
            MATCH (pn:{parent_node_label})
            WHERE pn.id = '{parent_node_id}'
            WITH pn
            LIMIT 1
            CREATE {create_node_lines},
                    {create_edge_lines}
            MERGE  (pn)-[:HAS_ELEM]->({root_node_name})
            RETURN {return_lines};""".format(
                parent_node_label=parent_node_label,
                parent_node_id=parent_node_id,
                create_node_lines=self.create_node_lines,
                create_edge_lines=self.create_edge_lines,
                root_node_name=cypher_node_name(self.nodes[0]),
                return_lines=self.return_lines
            ),
            'returns': [str, str, str]
            }
        # print(ret['q'])
        return ret
