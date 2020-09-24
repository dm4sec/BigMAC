#!/usr/bin/env python3

def plot(G, name, prune=False, debug=False, focus_set=set(), edge_limit=None):
    import networkx as nx

    # NetworkX has a relationship with pygraphviz's AGraph
    # This is a wrapper around graphviz (binary/library)
    # The python graphviz library is separate
    import pygraphviz

    remove_edges = False

    nx.set_node_attributes(G, 'filled,solid', 'style')

    if prune:
        while True:
            to_remove = []
            for n in G.nodes():
                if n.startswith("process") or n.startswith("subject"):
                    continue

                ie = set(map(lambda x: x[0], list(G.in_edges(n))))
                oe = set(map(lambda x: x[1], list(G.out_edges(n))))
                total = len(ie | oe)

                if total <= 1:
                    to_remove += [n]

            if len(to_remove) == 0:
                break

            list(map(G.remove_node, to_remove))

    if len(focus_set):
        to_keep = []

        for center_node in sorted(list(focus_set)):
            node_focus = set([center_node])
            node_focus |= set(map(lambda x: x[0], list(G.in_edges(center_node))))
            node_focus |= set(map(lambda x: x[1], list(G.out_edges(center_node))))

            for node in list(node_focus):
                if node != center_node and (node.startswith("process") or node.startswith("subject")):
                    node_focus |= set(map(lambda x: x[1], list(G.out_edges(node))))

            to_keep += [node_focus]

        from functools import reduce
        if len(to_keep) == 2:
            nodes_to_keep = (to_keep[0] & to_keep[1]) | focus_set
        else:
            nodes_to_keep = reduce(lambda x,y: x | y, to_keep)

        G = G.subgraph(list(nodes_to_keep))


    if edge_limit is not None and len(G.edges()) >= edge_limit:
        remove_edges = True

    if remove_edges:
        AG = nx.nx_agraph.to_agraph(nx.create_empty_copy(G))
    else:
        AG = nx.nx_agraph.to_agraph(G)

    if debug:
        from IPython import embed
        embed()


    # The SFDP program is extremely good at large graphs
    AG.layout(prog='sfdp')

    AG.draw(name, prog="sfdp", format='svg', args='-Gsmoothing=rng -Goverlap=prism2000 -Goutputorder=edgesfirst -Gsep=+2')

    #make_cute(G, show_labels=False)
    #AG = nx.nx_agraph.to_agraph(G)
    #AG.layout(prog='sfdp')
    #AG.draw('test2.svg', prog="sfdp", format='svg', args='-Gsmoothing=rng -Goverlap=prism2000 -Goutputorder=edgesfirst -Gsep=+2')

    #open('test.dot', 'w').write(AG.to_string())

    #from subprocess import Popen
    #p = Popen(['mingle', '-v', 'test.dot', '-o', 'wow.dot'])
    #p.communicate()

    #ag2 = pygraphviz.AGraph('wow.dot')
    #ag2.draw('test2.svg', prog='neato', format='svg', args='-Goverlap=false -Goutputorder=edgesfirst -n2')
