"""The library libdivgeo: the core of DivGeo with the C part of its Python
interface (modules/DivGeo/src/py), built without Motif and loaded with
ctypes.

Structures are read and written only through the table of fields that the
library gives (GetPyLayout): offsets and sizes come from its compiler, so
Python never assumes a layout."""

import ctypes
import os
import sys

import numpy as np

from . import api

_CTYPES = {("i", 4): ctypes.c_int, ("u", 8): ctypes.c_ulong,
           ("u", 4): ctypes.c_uint, ("d", 8): ctypes.c_double,
           ("p", 8): ctypes.c_void_p, ("p", 4): ctypes.c_void_p}


def default_path():
    """The library of the DivGeo build of this SOLPS-ITER session, in the
    build folder of the Python flavour (as the Makefile names it)."""
    env = os.environ
    folder = "%s.%s%s" % (env.get("HOST_NAME", ""), env.get("COMPILER", ""),
                          ".debug" if env.get("SOLPS_DEBUG") else "")
    name = "libdivgeo.dylib" if sys.platform == "darwin" else "libdivgeo.so"
    return os.path.join(env.get("SOLPSTOP", ""), "modules", "DivGeo",
                        "builds", folder, "python", name)


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
        self.rec_size = self.dll.GetPyRecSize()
        self.rec_dtype = self._rec_dtype()
        self.tools = dict(
            (name, ctypes.cast(getattr(self.dll, name), ctypes.c_void_p).value)
            for name in api.TOOLS)
        self.tool_names = dict((v, k) for k, v in self.tools.items())

    # Fields of the core structures

    def _ctype(self, name):
        offset, size, kind = self.fields[name]
        base = _CTYPES.get((kind, size))
        if base is None:
            base = _CTYPES[(kind, 8)] * (size // 8)
        return offset, base

    def get(self, ptr, name):
        offset, ctype = self._ctype(name)
        value = ctype.from_address(ptr + offset)
        if isinstance(value, ctypes.Array):
            return list(value)
        return value.value

    def set(self, ptr, name, value):
        offset, ctype = self._ctype(name)
        ctype.from_address(ptr + offset).value = value

    def obj_type(self, ptr):
        """Type code of a core object (its first int, GetObjType)."""
        return ctypes.c_int.from_address(ptr).value

    def string_at(self, ptr):
        return None if not ptr else ctypes.string_at(ptr).decode("latin-1")

    # Records of the view calls

    def _rec_dtype(self):
        names, formats, offsets = [], [], []
        for full, (offset, size, kind) in self.fields.items():
            st, _, field = full.partition(".")
            if st != "PyRec":
                continue
            if kind == "d":
                fmt = ("<f8", (size // 8,)) if size > 8 else "<f8"
            elif kind == "p":
                fmt = "<u%d" % size
            else:
                fmt = "<i%d" % size
            names.append(field)
            formats.append(fmt)
            offsets.append(offset)
        return np.dtype({"names": names, "formats": formats,
                         "offsets": offsets, "itemsize": self.rec_size})

    def take_records(self, first=0):
        """Copy of the records from index first on, and the text buffer;
        the buffers of the library change with the next core call."""
        recs = ctypes.c_void_p()
        txt = ctypes.c_void_p()
        ntext = ctypes.c_size_t()
        n = self.dll.TakePyRecs(ctypes.byref(recs), ctypes.byref(txt),
                                ctypes.byref(ntext))
        if n <= first:
            return np.zeros(0, self.rec_dtype), b""
        raw = (ctypes.c_char * (n * self.rec_size)).from_address(recs.value)
        arr = np.frombuffer(raw, dtype=self.rec_dtype, count=n)[first:].copy()
        text = ctypes.string_at(txt.value, ntext.value) if ntext.value else b""
        return arr, text

    def resources(self):
        """The resource lines compiled into the library (x_~fbr.c)."""
        arr = ctypes.cast(ctypes.addressof(
            ctypes.c_char_p.in_dll(self.dll, "dgResources")),
            ctypes.POINTER(ctypes.c_char_p))
        lines = []
        k = 0
        while arr[k] is not None:
            lines.append(arr[k].decode("latin-1"))
            k += 1
        return lines
