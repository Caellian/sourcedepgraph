#!/usr/bin/python

import networkx as nx
import matplotlib.pyplot as plt
import os.path
from pathlib import Path
import math
import argparse

SOURCE_FILES = [
    ".c++",
    ".cpp",
    ".cxx",
    ".cc",
    ".mm",
    ".c",
]
HEADER_FILES = [
    ".h++",
    ".hpp",
    ".hxx",
    ".hh",
    ".h",
]

# Source: https://en.cppreference.com/w/c/header
CSTDLIB = [
    "assert.h",
    "complex.h",
    "ctype.h",
    "errno.h",
    "fenv.h",
    "float.h",
    "inttypes.h",
    "iso646.h",
    "limits.h",
    "locale.h",
    "math.h",
    "setjmp.h",
    "signal.h",
    "stdalign.h",
    "stdarg.h",
    "stdatomic.h",
    "stdbit.h",
    "stdbool.h",
    "stdckdint.h",
    "stddef.h",
    "stdint.h",
    "stdio.h",
    "stdlib.h",
    "stdnoreturn.h",
    "string.h",
    "tgmath.h",
    "threads.h",
    "time.h",
    "uchar.h",
    "wchar.h",
    "wctype.h",
]

INCLUDE_PATHS=[
    "/usr/include",
    "/usr/local/include",
]

class Source(object):
    UNKNOWN = "unknown"
    LOCAL = "local"
    STDLIB = "stdlib"
    SYSTEM = "system"

def is_header(name):
    if "." not in name:
        return True
    for h in HEADER_FILES:
        if name.endswith(h):
            return True
    return False

def is_stdlib(name):
    return "." not in name or name in CSTDLIB

def is_system(name):
    for prefix in INCLUDE_PATHS:
        it = os.path.join(prefix, name)
        if os.path.isfile(it):
            return True
    return False

def process_indirect(graph):
    G = nx.DiGraph(graph)
    
    for node in graph.nodes():
        first = True
        for level in nx.bfs_successors(G, node):
            if first:
                first = False
                continue
            for v in level[1]:
                if is_stdlib(v):
                    continue
                G.add_edge(node, v, indirect=True, weight=100)
    
    return G

def resolve_file_path(name, source_dirs):
    for source_dir in source_dirs:
        path = os.path.join(source_dir, name)
        if os.path.isfile(path):
            return path
    return None

def build_graph(current, source_dirs, graph = None, parent = None, **options):
    G = graph or nx.DiGraph()
    
    path = resolve_file_path(current, source_dirs)
    header = is_header(current)
    source = Source.UNKNOWN
    
    includes = []
    if path is not None:
        with open(path, 'r') as file:
            for line in file.readlines():
                line = line.strip()
                if not line.startswith("#"):
                    continue
                
                # get macro name and check if it's #include
                macro_name = line.split(" ")[0]
                if macro_name != "#include":
                    continue
                
                include = line.split(" ")[1][1:-1]
                includes.append(include)
        source = Source.LOCAL

    source_file = None
    if source == Source.LOCAL and header and "check_sources" in options and options["check_sources"]:
        base_name = Path(current).stem
        for ext in SOURCE_FILES:
            source_path = resolve_file_path(base_name + ext, source_dirs)
            if source_path is not None:
                source_file = base_name + ext
                break

    if source == Source.UNKNOWN and is_stdlib(current):
        source = Source.STDLIB
        if "std-lib" not in options or not options["std-lib"]:
            return None
    if source == Source.UNKNOWN and is_system(current):
        source = Source.SYSTEM
        if "system" not in options or not options["system"]:
            return None

    if source == Source.UNKNOWN and "strict" in options and options["strict"]:
        return None
    
    G.add_node(current)
    if parent is not None:
        if header:
            G.add_edge(parent, current, weight=0.5)
        else:
            G.add_edge(parent, current, weight=0.2)
    G.nodes[current]["location"] = source
    G.nodes[current]["is_source"] = not header
    
    for include in includes:
        if not G.has_node(include):
            build_graph(include, graph = G, parent = current, source_dirs = source_dirs, **options)
        else:
            if "incidence" in G.nodes[include]:
                G.nodes[include]["incidence"] += 1
            else:
                G.nodes[current]["incidence"] = 1

    if source_file is not None and not G.has_node(source_file):
        build_graph(source_file, graph = G, parent = current, source_dirs = source_dirs, **options)
    
    if parent is not None:
        G.nodes[current]["incidence"] = 1
        return current
    else:
        return process_indirect(G)

def show_graph(H = None, out_file = None):
    d = nx.degree(H)
    pos = nx.spring_layout(H, weight="weight", k=4/math.sqrt(len(H)))

    nodesizes = []
    nodecolors = []
    
    for v, data in H.nodes(data = True):
        if "incidence" in data:
            nodesizes.append(data["incidence"] * 100)
        else:
            nodesizes.append(50)
        
        kind = H.nodes[v]["location"]
        if kind == Source.LOCAL:
            nodecolors.append("k")
        elif kind == Source.STDLIB:
            nodecolors.append("g")
        elif kind == Source.SYSTEM:
            nodecolors.append("b")
        else:
            nodecolors.append("r")
        
    edgestyles = []
    edgewidths = []
    edgealphas = []
    edgecolors = []
    for u, v, data in H.edges(data = True):
        if data is not None and data.get("indirect"):
            edgestyles.append("-.")
            edgecolors.append("#C0C0C0")
            edgealphas.append(0.2)
            edgewidths.append(1)
        else:
            is_source = H.nodes[v]["is_source"]
            
            if not is_source:
                edgestyles.append("solid")
                kind = H.nodes[v]["location"]
                if kind == Source.LOCAL:
                    edgecolors.append("k")
                    edgealphas.append(0.7)
                    edgewidths.append(4)
                elif kind == Source.STDLIB:
                    edgecolors.append("g")
                    edgealphas.append(0.4)
                    edgewidths.append(2)
                elif kind == Source.SYSTEM:
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
    
    nx.draw_networkx_edges(H, pos, alpha=edgealphas, width=edgewidths, style=edgestyles, edge_color=edgecolors)
    nx.draw_networkx_nodes(H, pos, node_size=nodesizes, node_color=nodecolors, alpha=0.9)
    label_options = {"ec": "k", "fc": "white", "alpha": 0.7}
    nx.draw_networkx_labels(H, pos, font_size=8, bbox=label_options)
    
    font = {"fontname": "Ubuntu", "color": "k", "fontweight": "bold", "fontsize": 14}
    ax.set_title("Include Map", font)

    plt.axis("off")
    
    if out_file is None:
        plt.show()
    else:
        plt.savefig(out_file, bbox_inches="tight")

def parse_args():
    parser = argparse.ArgumentParser(
                        prog="cdepgraph",
                    description="Generates include graph from C/C++ source files")
    
    parser.add_argument("SOURCE_DIRECTORY", help="Source directory containing program entry point")
    parser.add_argument("-m", "--main-file", help="Main file name and extension; default is any of main.c/cc/cpp/etc.")
    parser.add_argument("-i", "--include-paths", help="Semicolon (;) separated list of additional include paths")
    
    parser.add_argument("-l", "--std-lib", action="store_true", help="Include standard library includes in produced graph")
    parser.add_argument("-e", "--system", action="store_true", help="Include system includes in produced graph")
    
    parser.add_argument("-s", "--strict", action="store_true", help="Exclude includes which can't be found")
    parser.add_argument("-c", "--check-sources", action="store_true", help="Check includes of corresponding source files")
    
    parser.add_argument("-o", "--output", help="Output file name")
    parser.add_argument("-F", "--output-format", help="Output file format")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    source_dirs = [args.SOURCE_DIRECTORY]
    main_file = args.main_file
    
    if args.include_paths is not None:
        source_dirs.extend(args.include_paths.split(";"))
    
    if main_file is None:
        found = False
        for source_dir in source_dirs:
            for ext in SOURCE_FILES:
                main_file = os.path.join(source_dir, "main" + ext)
                if os.path.isfile(main_file):
                    found = True
                    main_file = "main" + ext
                    break
            
        if not found:
            print("Could not find entry point")
            return 1

    print("- Processing...")
    G = build_graph(main_file, source_dirs = source_dirs, **vars(args))
    print("- Drawing...")
    
    out = args.output
    fmt = args.output_format
    if out is not None and out.endswith(".dot") or fmt == "dot" or fmt == "graphviz":
        nx.nx_agraph.write_dot(G, out)
    elif out is not None and out.endswith(".gexf") or fmt == "gexf":
        nx.write_gexf(G, out)
    elif out is not None and out.endswith(".gml") or fmt == "gml":
        nx.write_gml(G, out)
    elif out is not None and out.endswith(".graphml") or fmt == "graphml":
        nx.write_graphml_lxml(G, out)
    elif out is not None and out.endswith(".graph6") or fmt == "graph6":
        nx.write_graph6(G, out)
    elif out is not None and out.endswith(".sparse6") or fmt == "sparse6":
        nx.write_graph6(G, out)
    elif out is not None and out.endswith(".net") or fmt == "pajek":
        nx.write_pajek(G, out)
    else:
        show_graph(G, out)

    print("Done.")
    return 0

if __name__ == "__main__":
    exit(main())
