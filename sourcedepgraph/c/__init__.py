import os

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

INCLUDE_PATHS = [
    "/usr/include",
    "/usr/local/include",
]


def file_path_resolver(name, source_dirs):
    for source_dir in source_dirs:
        path = os.path.join(source_dir, name)
        if os.path.isfile(path):
            return path
    return None


def find_includes(name, path, kind, source_dirs, **options):
    includes = []

    if path is None:
        return includes

    with open(path, 'r') as file:
        open_cfgs = []
        for line in file.readlines():
            line = line.strip()
            if not line.startswith("#"):
                continue

            # get macro name and check if it's #include
            macro_name = line.split(" ")[0]
            macro_content = line.removeprefix(macro_name + " ")

            if macro_name == "#include":
                include = macro_content[1:-1]
                includes.append(include)
            elif "flags" in options and options["flags"]:
                if macro_name == "#ifdef":
                    open_cfgs.append({
                        "kind": "ifdef",
                        "expr": f"defined({macro_content})",
                    })
                elif macro_name == "#ifndef":
                    open_cfgs.append({
                        "kind": "ifndef",
                        "expr": f"!defined({macro_content})",
                    })
                elif macro_name == "#if":
                    open_cfgs.append({
                        "kind": "if",
                        "expr": line.split(" ")[1],
                    })
                elif macro_name == "#else":
                    last = open_cfgs[-1]
                    open_cfgs.pop()
                    last["expr"] = f"!({last['expr']})"
                    open_cfgs.append(last)
                elif macro_name == "#endif":
                    open_cfgs.pop()


    if (kind == SourceKind.LOCAL_HEADER and
            "check_sources" in options and
            options["check_sources"]):
        base_name = Path(name).stem
        for ext in SOURCE_FILES:
            source_path = file_path_resolver(base_name + ext, source_dirs)
            if source_path is not None:
                includes.append(base_name + ext)
                break
    return includes


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


def detect_lang_from_sources(path):
    return True


def infer_source_kind(name, path):
    header = is_header(name)
    
    if path is not None and os.path.isfile(path):
        if header:
            return SourceKind.LOCAL_HEADER
        else:
            return SourceKind.LOCAL_SOURCE

    source_file = None
    if (source == Source.LOCAL and header and
            "check_sources" in options and
            options["check_sources"]):
        base_name = Path(name).stem
        for ext in SOURCE_FILES:
            source_path = resolve_file_path(base_name + ext, source_dirs)
            if source_path is not None:
                source_file = base_name + ext
                break

    if source == Source.UNKNOWN and is_stdlib(name):
        source = Source.STDLIB
        if "std-lib" not in options or not options["std-lib"]:
            return None
    if source == Source.UNKNOWN and is_system(name):
        source = Source.SYSTEM
        if "system" not in options or not options["system"]:
            return None
