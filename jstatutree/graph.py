import graphviz as viz

from collections import defaultdict
from . import etypes
from . import lawdata
import re
from pathlib import Path

def get_graph(elem, colorset, tree_name_factory, leaf_edges=True):
    item = elem.to_dot(lawname=tree_name_factory(elem), return_sides=True, colorset=colorset, return_clusters=True, return_leaves=True, leaf_edges=leaf_edges)
    assert len(item) == 5, str([type(v) for v in item])
    return {k:v for k,v in zip(['graph', 'head', 'tail', "clusters", "leaves"], item)}

def get_sample_leaf(leaves, tag):
    """
    for elem in elems:
        for leaf in elem.iterfind(".//Sentence"):
            if "/".join(Path().parts[3:]) in leaf.code:
                return leaf.code
    raise ValueError("Invalid tag: "+tag)
    """
    for leaf in leaves:
        if tag in leaf:
            return leaf
    return None

def cptable_graph(qelem, telems, code_pairs, sub_pairs=[], tree_name_factory=lambda x: "", h_align=False, layout='dot'):
    code_pairs = [item for item in code_pairs if sum((telem.code in item[0]) or (telem.code in item[1]) for telem in telems) > 0]
    G = viz.Digraph('comptable', filename="hoge")
    #omajinai
    G.body.append('\tgraph [ newrank=true compound=true; ];')
    G.body.append('\tnodesep=1.5;')
    G.body.append('\tlayout="{}";'.format(layout))
    G.node('Start', label='Start', style = 'invis')
    G.node('End', label='End', style = 'invis')
    colorset = defaultdict(lambda : 'black')
    colorset.update(
            {
                'Article': 'red',
                'Paragraph': 'darkorchid',
                'Item': 'darkorchid',
                'Sentence': 'blue'
        }
    )
    
    # graph construction
    
    query_graph = get_graph(qelem, colorset, tree_name_factory)
    target_graphs = {telem.code:get_graph(telem, colorset, tree_name_factory) for telem in telems}
    clusters = set(re.sub("^cluster_", "", c) for c in [c for g in target_graphs.values() for c in g["clusters"]]+query_graph["clusters"])
    leaves = set(c.code for c in [c for g in target_graphs.values() for c in g["leaves"]]+query_graph["leaves"])
    
    G.subgraph(query_graph['graph'])
    G.edge('Start', query_graph['head'].code, style = 'invis')
    G.edge(query_graph['tail'].code, 'End', style = 'invis')
    for tg in target_graphs.values():
        G.subgraph(tg['graph'])
        G.edge('Start', tg['head'].code, style = 'invis')
        G.edge(tg['tail'].code, 'End', style = 'invis')
    #print(clusters)
    align_list = []
    def put_align_list(al, item):
        if item in al:
            return
        nq, nt = item
        for i, (q, t) in enumerate(al):
            if q in nq and t in nt:
                al[i] = (nq, nt)
                break
        else:
            al.append((nq, nt))
                
    for item in code_pairs:
        if len(item) == 2:
            qcluster, tcluster = item
            label = ""
        elif len(item) == 3:
            qcluster, tcluster, label = item
            label = str(label)
        else:
            raise ValueError("Invalid code_pair "+str(item))
        qleaf, tleaf = get_sample_leaf(leaves, qcluster), get_sample_leaf(leaves, tcluster)
        if qleaf is None or tleaf is None:
            continue
        G.edge(
            qleaf, tleaf, label=str(label), 
            ltail=("cluster_"+qcluster) if qleaf != qcluster else None,
            lhead=("cluster_"+tcluster) if tleaf != tcluster else None,
        )
        if h_align:
            put_align_list(align_list,  (qcluster, tcluster))

    for item in sub_pairs:
        if len(item) == 2:
            qcluster, tcluster = item
            label = ""
        elif len(item) == 3:
            qcluster, tcluster, label = item
            label = str(label)
        else:
            raise ValueError("Invalid code_pair "+str(item))
        qleaf, tleaf = get_sample_leaf(leaves, qcluster), get_sample_leaf(leaves, tcluster)
        if qleaf is None or tleaf is None:
            continue
        G.edge(
            qleaf, tleaf, label=str(label), 
            ltail=("cluster_"+qcluster) if qleaf != qcluster else None,
            lhead=("cluster_"+tcluster) if tleaf != tcluster else None,
            style="dotted"
        )
        if h_align:
            put_align_list(align_list,  (qcluster, tcluster))
    max_ranks = {}
    for i,  l in enumerate(query_graph['leaves']):
        for qcluster, tcluster in align_list:
            #print(qcluster, l.code, qcluster in l)
            if qcluster in l.code:
                for tk, tg in target_graphs.items():
                    if tk not in tcluster:
                        continue
                    if max_ranks.get(tk, -1) < i:
                        #print(tk, i)
                        max_ranks[tk] = i 
                        #G.body.append('{rank=same;'+'"'+get_sample_leaf(leaves, qcluster)+'"'+'; '+'"'+get_sample_leaf(leaves, tcluster)+'"'+';}')
                    break
                break
    return G

def element2viz(root, lawname, _subgraph=True, return_sides=False, fusion_caption=True, colorset=None, return_clusters=False, return_leaves=False, leaf_edges=True):
    colorset = colorset or defaultdict(lambda : 'black')
    #print(colorset)
    clusters = []
    prev_cluster = None
    bottom_nodes = []
    elem_stack = [root]
    font = "IPAMincho"
    cluster_tag = 'cluster_'+str(root.code)
    clusters = [cluster_tag]
    sg = viz.Digraph(cluster_tag)
    sg.attr(label=lawname+etypes.code2jname(root.code)+root.caption)
    sg.attr(fontname=font)
    subgraph_stack = [(sg, lawname+etypes.code2jname(root.code))]
    subgraph_stack [-1][0]

    while len(elem_stack) > 0:
        target = elem_stack.pop()
        if target is None: # pop subgraph
            sg, _ = subgraph_stack.pop()
            subgraph_stack[-1][0].subgraph(sg)
            continue
        if fusion_caption and 'caption' in target.etype.lower():
            subgraph_stack[-1][0].attr(label=subgraph_stack[-1][1]+str(target.text))
        elif target.CATEGORY != etypes.CATEGORY_TEXT and len(list(target)) > 0:
            if subgraph_stack[-1][1] != lawname+etypes.code2jname(target.code):
                elem_stack.extend([None]+list(target)[::-1])
                cluster_tag = 'cluster_'+str(target.code)
                cluster_tag not in clusters and clusters.append(cluster_tag)
                sg =  viz.Digraph(cluster_tag)
                sg.attr(label=lawname+etypes.code2jname(target.code)+target.caption)
                sg.attr(color=colorset[target.etype])
                sg.attr(fontname=font)
                subgraph_stack.append((sg, lawname+etypes.code2jname(target.code)))
            else:
                elem_stack.extend(list(target)[::-1])
        else:
            texts = list(target.itertext())
            text = ''.join(texts if isinstance(texts[0], str) else [w for s in texts for w in s]) if len(texts) else ''
            subgraph_stack[-1][0].node(target.code,fontname=font, shape='box', color=colorset[target.etype], label='\n'.join([text[i:i+30] for i in range(0, len(text), 30)]  ))
            if leaf_edges and (len(bottom_nodes) > 0):
                if bottom_nodes[-1][1].name in subgraph_stack[-1][0].name:
                    bottom_nodes[-1][1].edge(bottom_nodes[-1][0].code, target.code, style = 'invis', weight='1000')
                #elif subgraph_stack[-1][0].name in bottom_nodes[-1][1].name :
                else:
                    subgraph_stack[-1][0].edge(bottom_nodes[-1][0].code, target.code, style = 'invis', weight='1000')
                #else:
                    #print(subgraph_stack[-1][0].name, bottom_nodes[-1][1].name )
                   # raise
            bottom_nodes.append((target, subgraph_stack[-1][0]))
    ret = subgraph_stack.pop()[0]
    leaves = [t for t, sg in bottom_nodes]
    if return_leaves:
        if return_clusters:
            return (ret, bottom_nodes[0][0], bottom_nodes[-1][0], clusters, leaves) if return_sides else  (ret, clusters, leaves)
        else:
            return (ret, bottom_nodes[0][0], bottom_nodes[-1][0], leaves) if return_sides else  (ret, leaves)
    else:


        if return_clusters:
            return (ret, bottom_nodes[0][0], bottom_nodes[-1][0], clusters) if return_sides else  (ret, clusters)    
        else:
            return (ret, bottom_nodes[0][0], bottom_nodes[-1][0]) if return_sides else  ret
    