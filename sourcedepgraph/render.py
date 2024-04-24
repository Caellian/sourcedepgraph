import matplotlib.pyplot as plt
import networkx as nx
import math
from __init__ import SourceKind


def show_graph(H=None, out_file=None):
    pos = nx.spring_layout(H, weight="weight", k=4/math.sqrt(len(H)))

    nodesizes = []
    nodecolors = []

    for v, data in H.nodes(data=True):
        if "incidence" in data:
            nodesizes.append(data["incidence"] * 100)
        else:
            nodesizes.append(50)

        kind = H.nodes[v]["kind"]
        if kind == SourceKind.LOCAL_HEADER or kind == SourceKind.LOCAL_SOURCE:
            nodecolors.append("k")
        elif kind == SourceKind.STDLIB:
            nodecolors.append("g")
        elif kind == SourceKind.SYSTEM:
            nodecolors.append("b")
        else:
            nodecolors.append("r")

    edgestyles = []
    edgewidths = []
    edgealphas = []
    edgecolors = []
    for u, v, data in H.edges(data=True):
        if data is not None and data.get("indirect"):
            edgestyles.append("-.")
            edgecolors.append("#C0C0C0")
            edgealphas.append(0.2)
            edgewidths.append(1)
        else:
            is_source = H.nodes[v]["is_source"]

            if not is_source:
                edgestyles.append("solid")
                kind = H.nodes[v]["kind"]
                if kind == SourceKind.LOCAL_HEADER:
                    edgecolors.append("k")
                    edgealphas.append(0.7)
                    edgewidths.append(4)
                elif kind == SourceKind.STDLIB:
                    edgecolors.append("g")
                    edgealphas.append(0.4)
                    edgewidths.append(2)
                elif kind == SourceKind.SYSTEM:
                    edgecolors.append("b")
                    edgealphas.append(0.4)
                    edgewidths.append(2)
                else:
                    edgecolors.append("r")
                    edgealphas.append(0.3)
                    edgewidths.append(1.5)
            else:
                edgestyles.append(":")
                edgecolors.append("k")
                edgealphas.append(0.7)
                edgewidths.append(4)

    fig, ax = plt.subplots(figsize=(12, 12))

    nx.draw_networkx_edges(H, pos, alpha=edgealphas, width=edgewidths,
                           style=edgestyles, edge_color=edgecolors)
    nx.draw_networkx_nodes(H, pos, node_size=nodesizes, node_color=nodecolors,
                           alpha=0.9)
    label_options = {"ec": "k", "fc": "white", "alpha": 0.7}
    nx.draw_networkx_labels(H, pos, font_size=8, bbox=label_options)

    font = {
        "fontname": "Ubuntu",
        "color": "k",
        "fontweight": "bold",
        "fontsize": 14
    }
    ax.set_title("Include Map", font)

    plt.axis("off")

    if out_file is None:
        plt.show()
    else:
        plt.savefig(out_file, bbox_inches="tight")
