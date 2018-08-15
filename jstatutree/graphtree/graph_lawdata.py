import sys, os
import os
import unicodedata
import re
import inspect
from jstatutree.xmltree import xml_lawdata, xml_etypes
from jstatutree.lawdata import SourceInterface, ReikiData, LawData
from jstatutree.myexceptions import LawError
from . import graph_etypes
from time import sleep
import multiprocessing
import traceback
from .cypherizer import TreeCypherizer
from neo4j.v1 import GraphDatabase
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
        self._code = node["code"]
        self.name= node["name"]
        self.lawnum = node["lawnum"]

    @property
    def prefecture_code(self):
        return re.split("/", self.code)[0]

    @property
    def municipality_code(self):
        return re.split("/", self.code)[1]

    @property
    def file_code(self):
        return re.split("/", self.code)[2]
from time import sleep
class JStatutreeGDB(object):
    def __init__(self, *args, **kwargs):
        exc = None
        for i in range(50):
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

    def __del__(self):
        self.close()

    def close(self):
        self.driver.close()
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
                },
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
            ret = session.read_transaction(self.load_govs).values()
            print(ret)
        cls = self.__class__
        cls.governments= [res['gcode'] for res in ret]

    @classmethod
    def init_db(cls, tx):
        for name, config in cls.INDEX_TYPE.items():
            if config['constraint'] == 'UNIQUE':
                query = 'CREATE CONSTRAINT ON (n:%s) ASSERT n.%s IS UNIQUE;' % (name, config['attrs'][0])
            else:
                query = 'CREATE INDEX ON :%s(%s);\n' % (name, ", ".join(config['attrs']))
            try:
                tx.run(query)
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
        return tx.run(query)

    @classmethod
    def reg_governments(cls, tx, code):
        if int(code) >= 10000:
            code_str = '{0:06}'.format(int(code))
            if code_str in cls.governments:
                return
            query = """
                merge (m:Municipalities{code: $code})
                merge (p:Prefectures{code: left(m.code, 2)})
                merge (p)-[:PREF_OF]->(m)
                return m.code, p.code
            """
            record = tx.run(query, code=code_str)[0]
            mcode, pcode = record['m.code'], record['p.code']
            mcode not in cls.governments and cls.governments.append(mcode)
            pcode not in cls.governments and cls.governments.append(pcode)
            print('reg gov:', mcode)
        else:
            code_str = '{0:02}'.format(int(code))
            if code_str in cls.governments:
                print('skip reg gov: ', code_str)
                return
            if code_str in cls.governments:
                return
            query = """
                MERGE (p:Prefectures{code: $code}
                RETURN p.code
            """
            record = tx.run(query, code=code_str)[0]
            pcode = record['p.code']
            pcode not in cls.governments and cls.governments.append(pcode)
            print('reg gov:', pcode)

    def reg_lawdata(self, lawdata):
        with self.driver.session as session:
            sessiion.write_transaction(self.reg_governments, lawdata.municipality_code)
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
            res = session.run(query)
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
        if len(result) != 1:
            return None
        return GDBReikiData(result[0]['stat'])

    def check_registered(self, path=None, lawdata=None):
        assert not (path is None and lawdata is None), "You must give an xml path or a lawdata as an argument."
        if path is not None:
            tmp, fcode = os.path.split(path)
            mcode = os.path.split(tmp)[1]
        else:
            mcode, fcode = lawdata.municipality_code, lawdata.file_code
        return self.load_lawdata(self, mcode, fcode) is not None

    def register_paths(self, paths, levels, valid_vnode, only_reiki, tx_size_limit):
        cypherizer = TreeCypherizer(levels, valid_vnode, only_reiki, tx_size_limit)
        for path in paths:
            reader=xml_lawdata.ReikiXMLReader(path)
            lawdata = self.load_lawdata(path)
            if lawdata is None:
                cypherizer.submit_reader(reader)
            else:
                print("skip(exists):", lawdata.name)
        cypher_generator = self.submit_reader(reader)
        with self.driver.session() as session:
            for lawdata, cypher_generator in cypherizer:
                lawdata_id = session.write_transaction(self.reg_lawdata, lawdata)
                cypher_generator.send(lawdata_id)
                while True:
                    query = cypher_generator.send(session.run(query).single())
                    if query is None:
                        break
                session.write_transaction(cls.mark_tree, lawdata_id)
                print("register:", lawdata.name)

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
from multiprocessing import Queue

def register_directory(levels, basepath, loginkey, workers, only_reiki, only_sentence, chunk_size=20):
    writer = MultiProcReikiWriter(loginkey, levels, only_reiki=only_reiki, only_sentence=only_sentence, workers=workers, chunk_size=chunk_size)
    writer.submit_paths(basepath)
    writer.run()
from threading import Thread
MAX_CHUNK_SIZE = 5
class MultiProcReikiWriter(object):
    def __init__(self, loginkey, levels, only_reiki=True, only_sentence=True, workers=None, chunk_size=MAX_CHUNK_SIZE):
        self.loginkey=loginkey
        self.levels = levels
        self.only_reiki = only_reiki
        self.only_sentence = only_sentence
        self.workers = workers if workers  is not None else multiprocessing.cpu_count()
        self.executors = concurrent.futures.ProcessPoolExecutor(max_workers=self.workers)
        self.xmlpath_chunks_queue = Queue(100)
        self.chunk_size = chunk_size
        self.path_submit_queue = Queue(chunk_size*100)
        self.enqueue_thread = Thread(target=self.enqueue_paths, daemon=True)
        self.enqueue_thread.start()

    def submit_paths(self, *paths):
        for path in paths:
            print("submit path:", path)
            self.path_submit_queue.put(path)

    def enqueue_paths(self):
        print("start enqueue thread")
        chunk = []
        while True:
            item = self.path_submit_queue.get()
            if item is None:
                len(chunk) > 0 and self.xmlpath_chunks_queue.put(chunk)
                self.xmlpath_chunks_queue.put(None)
                continue
            # print("extract path:", item)
            for xml_path in list(find_all_files(item, [".xml"])):
                if len(chunk) < self.chunk_size:
                    chunk.append(xml_path)
                else:
                    # print("enqueue path chunk")
                    self.xmlpath_chunks_queue.put(chunk)
                    chunk = []

    @staticmethod
    def exec_main(paths, levels, valid_vnode, only_reiki, chunk_size, loginkey):
        print("login")
        gdb = ReikiGDB(loginkey)
        print("register begin")
        gdb.register_paths(paths, levels, valid_vnode, only_reiki, chunk_size)

    def get_future_results(self, futures, timeout=None):
        put_cancelled = lambda f: self.submit_paths(*f.arg_paths)
        all_succeeded_flag = True
        for future in futures:
            print('proc-future', future.task_number, 'finished')
            try:
                future.result(timeout=timeout)
                print('proc-future', future.task_number, 'succeed')
            except concurrent.futures.TimeoutError:
                print('proc-future', future.task_number, 'timeout and retry')
                put_cancelled(future)
                all_succeeded_flag = False
            except concurrent.futures.CancelledError:
                print('proc-future', future.task_number, 'canncelled and retry')
                put_cancelled(future)
                all_succeeded_flag = False
            except KeyError:
                print('proc-future', future.task_number, 'raised and retry')
                put_cancelled(future)
                all_succeeded_flag = False
            except Exception:
                print('proc-future', future.task_number, 'raised and retry')
                traceback.print_exc()
                put_cancelled(future)
                all_succeeded_flag = False
        return all_succeeded_flag

    def end_submit_path(self):
        self.submit_paths(None)

    def run(self):
        trial_count = 0
        end_flag = False
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers) as proc_exec:
            while not end_flag:
                print("trial:", trial_count)
                task_count = 0
                futures = []
                self.end_submit_path()
                while True:
                    paths = self.xmlpath_chunks_queue.get()
                    # print(paths)
                    if paths is None:
                        break
                    future = proc_exec.submit(
                                self.exec_main,
                                paths=paths,
                                levels=self.levels,
                                valid_vnode=True,
                                only_reiki=self.only_reiki,
                                chunk_size=self.chunk_size,
                                loginkey=self.loginkey
                            )
                    future.arg_paths = paths
                    future.task_number = task_count
                    futures.append(future)
                    # print("submit: task", task_count)
                    task_count += 1
                print("task wait")
                waited = concurrent.futures.wait(futures, timeout=self.chunk_size*len(futures)/self.workers*2)
                done, not_done = list(waited.done), list(waited.not_done)
                end_flag = self.get_future_results(done)
                for future in not_done:
                    if future.done():
                        continue
                    future.cancel()
                end_flag = end_flag and self.get_future_results(not_done)
