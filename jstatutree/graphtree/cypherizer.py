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


class TreeCypherizer(object):
    EXECUTOR = ThreadPoolExecutor(max_workers=5)

    def __init__(self, levels, valid_vnode=True, only_reiki=True, tx_size_limit=20, only_sentence=True):
        self.levels = levels
        self.valid_vnode = valid_vnode
        self.tx_size_limit = tx_size_limit
        self.only_reiki = only_reiki
        self.only_sentence = only_sentence
        self.node_num = {}
        self.tasks = []

    @staticmethod
    def cypher_result_map(res):
        if not isinstance(res, list):
            res = res.values()[0]
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

    @staticmethod
    def iter_rollback_cyphers(node_infos):
        for key, value in node_infos.items():
            yield """MATCH (n:%s{id: '%s'}) DETACH DELETE n""" % (value['parent_node_label'], value['parent_node_id'])


    @classmethod
    def gen_cyphers(cls, cyphers):
        node_infos = {}
        lawdata_id = yield node_infos
        node_infos.update({'lawdata_node': {'parent_node_label': 'Statutories', 'parent_node_id':lawdata_id}})
        for cypher in cyphers:
            res = yield cypher.query(**node_infos[str(cypher.require_node)])
            node_infos.update(cls.cypher_result_map(res))
        yield None
        raise StopIteration

    def submit_reader(self, reader):
        if reader.is_closed():
            reader.open()
            if reader.is_closed():
                # print('skip(cannot open): '+str(reader.lawdata.name))
                return False
        if self.only_reiki and not reader.lawdata.is_reiki():
            # print('skip(not reiki): '+str(reader.lawdata.name))
            reader.close()
            return False
        # self.submit_reader(reader)
        future = self.__class__.EXECUTOR.submit(self._cypherize, reader)
        self.tasks.append(future)

    def _cypherize(self, reader):
        try:
            err = None
            if reader.is_closed():
                reader.open()
                if reader.is_closed():
                    return False, str('ERROR cannot open')+str(reader.path)
            root = reader.get_tree()
            nodes = list(root.depth_first_iteration(self.levels, valid_vnode=self.valid_vnode))
            reader.close()
        except LawError as err:
            reader.close()
            return False, str(err)
        except Exception as e:
            reader.close()
            return False, traceback.format_exc()
        self.node_num[reader.lawdata.code] = 0
        cypher = TreeCypher(self, 'lawdata_node')
        cyphers = []
        cypher.add_root(nodes[0])
        for node in nodes[1:]:
            if cypher.add_node(node):
                continue
            cyphers.append(cypher)
            cypher = TreeCypher(self)
            cypher.add_root(node)
        cyphers.append(cypher)
        generator = self.gen_cyphers(cyphers)
        return True, (reader.lawdata, generator)

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
        self.node_var_names = dict()
        self.require_node = require_node

    def __len__(self):
        return len(self.edges) + len(self.nodes)

    def get_node_var_name(self, node):
        return self.node_var_names[cypher_node_name(node)]

    def create_cypher(self, node):
        node_id = self.cypherizer.get_node_id(node.lawdata.code)
        node_var_name = node.etype.__name__+os.path.split(node_id)[1]
        self.node_var_names[cypher_node_name(node)] = node_var_name
        return ''.join([
            """(%s:%s:Elements{""" % (node_var_name, node.etype.__name__ + 's'),
            """name: '%s',""" % (node.name if node.name!='' else node.etype.__name__),
            """fullname: '%s',""" % str(node),
            """num: '%s',""" % str(node.num.num),
            """text: '%s',""" % node.text,
            """fulltext: '%s',""" % ''.join(node.iter_sentences()),
            """etype: '%s',""" % node.etype.__name__,
            """id: '%s'""" % (node_id),
            """})"""
            ])

    def cypher_node_edge(self, srcnode, tarnode):
        src_node_name = srcnode if isinstance(srcnode, str) else self.get_node_var_name(srcnode)
        tar_node_name = tarnode if isinstance(tarnode, str) else self.get_node_var_name(tarnode)
        return '(%s)-[:HAS_ELEM]->(%s)' % (src_node_name, tar_node_name)

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
                l.append(self.cypher_node_edge('pn', n2))
            else:
                l.append(self.cypher_node_edge(n1, n2))
        return ',\n\t'.join(l)

    @property
    def return_lines(self):
        return ',\n\t'.join([
                "{node_name}.fullname, {node_name}.etype, {node_name}.id".format(
                        node_name=self.get_node_var_name(n),
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
                root_node_name=self.get_node_var_name(self.nodes[0]),
                return_lines=self.return_lines
            )
