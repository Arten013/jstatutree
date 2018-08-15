import os
import re
from jstatutree.xmltree import xml_lawdata
from jstatutree.myexceptions import LawError
from queue import Queue
from time import sleep
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

def cypher_node_name(node):
    return re.sub('[()]', '', re.sub('/', '_', node.code[15:]))

def cypher_node_edge(srcnode, tarnode):
    src_node_name = srcnode if isinstance(srcnode, str) else cypher_node_name(srcnode)
    tar_node_name = tarnode if isinstance(tarnode, str) else cypher_node_name(tarnode)
    return '(%s)-[:HAS_ELEM]->(%s)' % (src_node_name, tar_node_name)

class TreeCypherizer(object):
    EXECUTOR = ThreadPoolExecutor(max_workers=5)

    def __init__(self, levels, valid_vnode=True, only_reiki=True, tx_size_limit=20, only_sentence=True):
        self.levels = levels
        self.valid_vnode = valid_vnode
        self.tx_size_limit = tx_size_limit
        self.only_reiki = only_reiki
        self.only_sentence = only_sentence
        self.gdb = gdb
        self.node_num = {}
        self.tasks = []

    @staticmethod
    def cypher_result_map(result):
        return {
                res[3*i]: {
                    'parent_node_label': res[3*i+1]+'s',
                    'parent_node_id': str(res[3*i+2])
                    }
                for i in range(len(res)//3)
                }

    def __iter__(self):
        for future in as_completed(self.tasks):
            yield future.result()
        raise StopIteration

    @classmethod
    def gen_cyphers(cls, cyphers):
        lawdata_id = yield None
        qres = yield cyphers[0].query('Statutories', lawdata_id)
        node_infos = cls.cypher_result_map(qres)
        for cypher in cyphers:
            additional_node_infos = yield cypher.query(**node_infos[str(cypher.require_node)])
            node_infos.update(additional_node_infos)
        yield None
        raise StopIteration

    def submit_reader(self, reader):
        if reader.is_closed():
            reader.open()
            if reader.is_closed():
                print('skip(cannot open): '+str(reader.lawdata.name))
                return False
        if self.only_reiki and not reader.lawdata.is_reiki():
            print('skip(not reiki): '+str(reader.lawdata.name))
            reader.close()
            return False
        self.submit_reader(reader)
        future = self.__class__.EXECUTOR.submit(_cypherize, reader)
        self.tasks.append(futures)

    def _cypherize(self, reader):
        try:
            root = reader.get_tree()
            nodes = list(root.depth_first_iteration(self.levels, valid_vnode=self.valid_vnode))
        except LawError as e:
            ret = False, str(e), None
        except Exception as e:
            ret = False, traceback.format_exc(), None
        finally:
            reader.close()
        self.node_num[reader.lawdata.code] = 0
        cyphers = [TreeCypher(self, 'lawdata_node')]
        cyphers[0].add_root(nodes[0])
        for node in nodes[1:]:
            if cypher.add_node(node):
                continue
            cyphers.append(cypher)
            cypher = TreeCypher(self)
            cypher.add_root(node)
        cyphers.append(cypher)
        return (reader.lawdata, self.gen_cyphers(cyphers))

    def get_node_id(self, lawcode):
        ret = lawcode+'/'+str(self.node_num[lawcode])
        self.node_num[lawcode] += 1
        return ret


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
            """(%s:%s:Elements{""" % (cypher_node_name(node), node.etype.__name__ + 's'),
            """name: '%s',""" % (node.name if node.name!='' else node.etype.__name__),
            """fullname: '%s',""" % str(node),
            """num: '%s',""" % str(node.num.num),
            """text: '%s',""" % node.text, #(node.text if len(node.text) < 5 else node.text[:5]),
            """fulltext: '%s',""" % ''.join(node.iter_sentences()),#[:5],
            """etype: '%s',""" % node.etype.__name__,
            """id: '%s'""" % (self.cypherizer.get_node_id(node.lawdata.code)),
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
        return """
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
            )
