"""The library libamds: the core of AMDS with the C part of its Python
interface (modules/amds/src/py), built without Motif and loaded with
ctypes.

Structures are read and written only through the table of fields that the
library gives (GetPyLayout): offsets and sizes come from its compiler, so
Python never assumes a layout."""

import ctypes
import os
import sys

from . import api

_CTYPES = {("i", 4): ctypes.c_int, ("u", 8): ctypes.c_ulong,
           ("p", 8): ctypes.c_void_p, ("p", 4): ctypes.c_void_p}


def build_folder():
    """The AMDS build folder of this SOLPS-ITER session (as the Makefile
    names it)."""
    env = os.environ
    folder = "%s.%s%s" % (env.get("HOST_NAME", ""), env.get("COMPILER", ""),
                          ".debug" if env.get("SOLPS_DEBUG") else "")
    return os.path.join(env.get("SOLPSTOP", ""), "modules", "amds",
                        "builds", folder)


def default_path():
    """The library of the AMDS build of this SOLPS-ITER session, in the
    folder of the Python flavour."""
    name = "libamds.dylib" if sys.platform == "darwin" else "libamds.so"
    return os.path.join(build_folder(), "python", name)


def build_problems(path):
    """Why the library of this session cannot be loaded (empty if it can):
    environment, a build made with Motif last (stamp of the Makefile), a
    library not built."""
    missing = [v for v in ("SOLPSTOP", "HOST_NAME", "COMPILER")
               if not os.environ.get(v)]
    if missing:
        return [", ".join(missing) + " not set: source setup.csh first"]
    build = build_folder()
    if os.path.isfile(os.path.join(build, ".gui_motif")):
        return ["%s was built with Motif (USE_MOTIF): the Python interface "
                "needs a build without USE_MOTIF" % build]
    if not os.path.isfile(path):
        return ["libamds not built: run gmake amds in $SOLPSTOP "
                "(no %s)" % path]
    return []


def text(value):
    """Python text of a core string (bytes or None)."""
    return None if value is None else value.decode("latin-1")


def cstr(value):
    """Core string of a Python text (None stays None)."""
    return None if value is None else value.encode("latin-1")


class Library:
    def __init__(self, path):
        self.path = path
        self.dll = ctypes.CDLL(path)
        api.declare(self.dll)
        self.fields = {}
        k = 0
        while True:
            name = ctypes.c_char_p()
            offset = ctypes.c_size_t()
            size = self.dll.GetPyLayout(k, ctypes.byref(name),
                                        ctypes.byref(offset))
            if size == 0:
                break
            kind = self.dll.GetPyLayoutType(k).decode()
            self.fields[name.value.decode()] = (offset.value, size, kind)
            k += 1

    # Fields of the core structures

    def get(self, ptr, name):
        offset, size, kind = self.fields[name]
        return _CTYPES[(kind, size)].from_address(ptr + offset).value

    def set(self, ptr, name, value):
        offset, size, kind = self.fields[name]
        _CTYPES[(kind, size)].from_address(ptr + offset).value = value

    def string(self, ptr, name):
        """A string field (char*) as text."""
        p = self.get(ptr, name)
        return None if not p else ctypes.string_at(p).decode("latin-1")

    def group(self, g):
        """The members of a core Group, in order."""
        dll = self.dll
        return [dll.GroupAt(g, k) for k in range(dll.PyGroupCount(g))]

    @staticmethod
    def positions(pos):
        """A C array of list positions."""
        return (ctypes.c_int * max(len(pos), 1))(*pos), len(pos)

    def resources(self):
        """The resource lines compiled into the library (x_~fbr.c)."""
        arr = ctypes.cast(ctypes.addressof(
            ctypes.c_char_p.in_dll(self.dll, "amdsResources")),
            ctypes.POINTER(ctypes.c_char_p))
        lines = []
        k = 0
        while arr[k] is not None:
            lines.append(arr[k].decode("latin-1"))
            k += 1
        return lines

    @staticmethod
    def exit(code):
        """The end as exit() of the Motif program: every stream written
        (Python, then the C streams of the core), then the process ends
        (the core leaves no exit handler that writes)."""
        sys.stdout.flush()
        sys.stderr.flush()
        ctypes.CDLL(None).fflush(None)
        os._exit(code)
