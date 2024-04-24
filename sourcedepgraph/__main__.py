import sys
import argparse
from __init__ import *
from render import show_graph
import networkx as nx
import os.path


def parse_args():
    parser = argparse.ArgumentParser(
                    prog="cdepgraph",
                    description="Generates include graph from C/C++ source"
                                "files")

    parser.add_argument("SOURCE_DIRECTORY",
                        help="Source directory containing program entry point"
                             "or project configuration file")
    parser.add_argument("-m", "--main-file",
                        help="Main file name and extension; default is any of"
                             "main.c/cc/cpp/etc.")
    parser.add_argument("-i", "--include-paths",
                        help="Semicolon (;) separated list of additional"
                             "include paths/projects")

    parser.add_argument("-l", "--std-lib", action="store_true",
                        help="Include standard library includes in produced"
                             "graph")
    parser.add_argument("-e", "--system", action="store_true",
                        help="Include system includes in produced graph")

    parser.add_argument("-s", "--strict", action="store_true",
                        help="Exclude includes which can't be found")
    parser.add_argument("-c", "--check-sources", action="store_true",
                        help="Check includes of corresponding source files")
    parser.add_argument("-f", "--flags", action="store_true",
                        help="Store required compiler flags in graph edges")

    parser.add_argument("-o", "--output",
                        help="Output file name")
    parser.add_argument("-F", "--output-format",
                        help="Output file format")

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
    G = build_graph(main_file, source_dirs=source_dirs, **vars(args))
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
    sys.exit(main())