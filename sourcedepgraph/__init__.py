#!/usr/bin/python

import networkx as nx
import importlib
import os.path
from pathlib import Path
from types import FunctionType
from dataclasses import dataclass


@dataclass
class Language:
    name: str
    detect_lang_from_sources: FunctionType
    infer_source_kind: FunctionType
    file_path_resolver: FunctionType
    find_includes: FunctionType


# Will be populated from `lang` file
LANGUAGES = []


def init_languages():
    langs = []
    lang_path = os.path.join(Path(__file__).parent.resolve(), "lang")
    with open(lang_path, 'r') as file:
        langs = file.read().splitlines()

    for lang in langs:
        module = importlib.import_module(lang, "sourcedepgraph")
        LANGUAGES.append(Language(
            name=lang,
            detect_lang_from_sources=module.detect_lang_from_sources,
            infer_source_kind=module.infer_source_kind,
            file_path_resolver=module.file_path_resolver,
            find_includes=module.find_includes,
        ))


init_languages()


class SourceKind(object):
    UNKNOWN = "unknown"
    LOCAL_HEADER = "header-local"
    LOCAL_SOURCE = "source-local"
    STDLIB = "header-stdlib"
    SYSTEM_HEADER = "header-system"
    LIBRARY = "library"


@dataclass
class Include:
    path: str
    conditions: list


def proc_cfgs(cfgs):
    return " && ".join(map(lambda it: it.expr, cfgs))


def build_source_graph(current, source_dirs, graph=None, parent=None,
                       language=None, **options):
    if language is None:
        raise ValueError("Language is not specified")

    G = graph or nx.DiGraph()

    path = language.file_path_resolver(current, source_dirs)
    kind = language.infer_source_kind(current, path)
    includes = language.find_includes(current, path, kind, source_dirs, **options)

    if (kind == SourceKind.UNKNOWN and
            "strict" in options and options["strict"]):
        return None

    G.add_node(current)
    if parent is not None:
        if kind == SourceKind.LOCAL_HEADER:
            G.add_edge(parent, current, weight=0.5)
        else:
            G.add_edge(parent, current, weight=0.2)
    G.nodes[current]["kind"] = kind

    for include in includes:
        if not G.has_node(include):
            build_source_graph(include, graph=G, parent=current,
                               source_dirs=source_dirs, **options)
            G.nodes[include]["incidence"] = 1
        else:
            if "incidence" in G.nodes[include]:
                G.nodes[include]["incidence"] += 1
            else:
                G.nodes[current]["incidence"] = 1

    if parent is not None:
        G.nodes[current]["incidence"] = 1
        return current
    else:
        return G
