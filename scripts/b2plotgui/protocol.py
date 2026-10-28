"""Binary message protocol between b2pl_gui.exe and b2plot.py.

Every message is ``int32 opcode | int32 nbytes | payload``, in native byte
order. The payload layouts are written by b2mod_b2plot_gui.F and
ncar_gui.F (modules/B2.5/src) and are listed in SPECS below.
"""

import re
import struct
from dataclasses import dataclass, field

import numpy as np

from . import PROTOCOL_VERSION

MAGIC = 1110593607

# Opcode -> (name, payload fields). A field type is i4, r4, r8 or str,
# optionally followed by [count], where count is a field name or a
# product of field names already decoded.
SPECS = {
    1: ("HELLO", "magic:i4 version:i4 producer:str"),
    2: ("RUNINFO", "nCv:i4 nCi:i4 nFc:i4 nVx:i4 isClassicalGrid:i4 nx:i4 "
                   "ny:i4 ns:i4 natm:i4 nmol:i4 nion:i4 ntrii:i4 nbnd:i4 "
                   "with_eirene:i4 time:r8 label:str nsp:i4 "
                   "species:str[nsp]"),
    3: ("SYNC", "id:i4 depth:i4[7] toplabel:str top_nz:i4"),
    4: ("BYE", ""),
    5: ("CATALOG", None),
    6: ("MESSAGE", "level:i4 text:str"),
    10: ("FRAME", ""),
    11: ("PAGE_META", "title:str xlabel:str ylabel:str extralabel:str "
                      "globalheader:str linlog:i4 physical:i4 aspect:i4 "
                      "colorbar:i4 ix_page:i4 iy_page:i4 nx_page:i4 "
                      "ny_page:i4 xwidth:r4 yheight:r4 xlo:r4 xhi:r4 "
                      "ylo:r4 yhi:r4"),
    12: ("SET", "vl:r4 vr:r4 vb:r4 vt:r4 wl:r4 wr:r4 wb:r4 wt:r4 lf:i4"),
    20: ("COLOR_REP", "ci:i4 r:r4 g:r4 b:r4"),
    21: ("PLCI", "ci:i4"),
    22: ("LWSC", "w:r4"),
    23: ("LN", "ltype:i4"),
    24: ("DASH", "ipat:str jcrt:i4 jsize:i4"),
    25: ("FACI", "ci:i4"),
    26: ("FAIS", "ints:i4"),
    27: ("PMCI", "ci:i4"),
    28: ("MK", "mtype:i4"),
    29: ("MKSC", "scale:r4"),
    30: ("TXFP", "font:i4 prec:i4"),
    31: ("PCSET", "pname:str kind:i4 ival:i4 cval:str"),
    32: ("GASET", "pname:str kind:i4 ival:i4 rval:r4"),
    33: ("SFSET", "pname:str ival:i4"),
    34: ("CHATTR", "which:i4 a:r4 b:r4"),
    40: ("LINE", "xa:r4 ya:r4 xb:r4 yb:r4"),
    41: ("POLYLINE", "n:i4 x:r4[n] y:r4[n]"),
    42: ("LASTD", ""),
    43: ("FILL", "n:i4 x:r4[n] y:r4[n] ci:i4 tagkind:i4 tagindex:i4 "
                 "tagvalue:r8"),
    44: ("MARKERS", "n:i4 x:r4[n] y:r4[n]"),
    45: ("TEXT", "x:r4 y:r4 size:r4 angd:r4 cntr:r4 chrs:str"),
    46: ("GKSTEXT", "x:r4 y:r4 chrs:str"),
    47: ("AXES", "mjrx:i4 mnrx:i4 mjry:i4 mnry:i4 ixlb:i4 iylb:i4 igph:i4 "
                 "xint:r4 yint:r4 fmtx:str fmty:str numx:i4 numy:i4 "
                 "iszx:i4 iszy:i4 ixdc:i4 iydc:i4 ixor:i4"),
    48: ("COLORBAR", "ihov:i4 xleb:r4 xreb:r4 ybeb:r4 yteb:r4 nbox:i4 "
                     "wsfb:r4 hsfb:r4 lfin:i4[nbox] iftp:i4 nlbs:i4 "
                     "llbs:str[nlbs] lbab:i4"),
    49: ("CELLARRAY", "xp1:r4 yp1:r4 xp2:r4 yp2:r4 nxclr:i4 nyclr:i4 "
                      "ixclr:i4 iyclr:i4 nxdo:i4 nydo:i4 "
                      "clria:i4[nxclr*nyclr]"),
    50: ("CT_MESH", "npnt:i4 lopn:i4 nedg:i4 loen:i4 ntri:i4 lotn:i4 "
                    "rpnt:r4[npnt] iedg:i4[nedg] itri:i4[ntri]"),
    51: ("CP_RECT", "kzdt:i4 mzdt:i4 nzdt:i4 zdat:r4[kzdt*nzdt]"),
    52: ("AREA_EDGE", "igrp:i4 idl:i4 idr:i4 n:i4 x:r4[n] y:r4[n]"),
    53: ("CONTOUR_FILL", "source:i4 ncl:i4 clv:r4[ncl] aia:i4[ncl] "
                         "aib:i4[ncl] nid:i4 color:i4[nid] xc1:r4 xcm:r4 "
                         "yc1:r4 ycn:r4 spv:r4 map:i4"),
    54: ("CONTOUR_LINES", "source:i4 ncl:i4 clv:r4[ncl] clu:i4[ncl] "
                          "cll:r4[ncl] plci:i4 llp:i4 llo:i4 xc1:r4 xcm:r4 "
                          "yc1:r4 ycn:r4 spv:r4 map:i4"),
    55: ("CONTOUR_INFO", "source:i4 ilt:str ilx:r4 ily:r4 ilp:i4 llp:i4 "
                         "llo:i4"),
    56: ("AREA_INIT", ""),
    60: ("SEG_OPEN", "ib:i4"),
    61: ("SEG_CLOSE", ""),
    62: ("SEG_INSERT", "ib:i4"),
    70: ("GEOMETRY", "nCv:i4 nVx:i4 isClassicalGrid:i4 vxX:r4[nVx] "
                     "vxY:r4[nVx] haspsi:i4 psin:r4[nVx] ncell:i4 "
                     "cells:i4[ncell] nv:i4[ncell] nlist:i4 vlist:i4[nlist] "
                     "cx:r4[ncell] cy:r4[ncell] reg:i4[ncell] ix:i4[ncell] "
                     "iy:i4[ncell] nxpt:i4 xpt:r4[nxpt*2]"),
    71: ("OVERLAY_BEGIN", "role:i4 name:str"),
    72: ("OVERLAY_END", ""),
    73: ("TRIMESH", "nknot:i4 x:r4[nknot] y:r4[nknot] ntri:i4 "
                    "tri:i4[ntri*3]"),
    74: ("FIELD", "label:str location:i4 n:i4 ncol:i4 columns:str[ncol] "
                  "values:r4[n*ncol] nvx:i4 vertex:r4[nvx*ncol]"),
    75: ("VECTOR", "label:str label2:str location:i4 n:i4 ncol:i4 "
                   "columns:str[ncol] "
                   "vr:r4[n*ncol] vz:r4[n*ncol] nvx:i4 vxr:r4[nvx*ncol] "
                   "vxz:r4[nvx*ncol]"),
    77: ("PSIMAP", "nr:i4 nz:i4 r:r4[nr] z:r4[nz] psin:r4[nr*nz] ro:r4 zo:r4 "
                   "rs:r4 zs:r4"),
    78: ("LEVELS", "kind:i4 n:i4 lev:r4[n]"),
    79: ("MOVIEINFO", "file:i4 path:str nt:i4 times:r8[nt] nvar:i4"),
    80: ("MOVIEVAR", "file:i4 var:str long:str units:str location:i4 "
                     "ncol:i4 dim:str"),
}

NAMES = {op: spec[0] for op, spec in SPECS.items()}
OPCODES = {name: op for op, name in NAMES.items()}

_FIELD = re.compile(r"^(\w+):(i4|r4|r8|str)(?:\[([\w*]+)\])?$")
_DTYPES = {"i4": np.dtype("=i4"), "r4": np.dtype("=f4"), "r8": np.dtype("=f8")}


class ProtocolError(Exception):
    """Malformed or incompatible message stream."""


class ProtocolEOF(ProtocolError):
    """The stream ended inside a message."""


def _parse(spec):
    fields = []
    for item in spec.split():
        m = _FIELD.match(item)
        if not m:
            raise ValueError(f"bad field spec {item!r}")
        fields.append(m.groups())
    return fields


FIELDS = {op: (_parse(s) if s is not None else None)
          for op, (_, s) in SPECS.items()}


@dataclass
class Message:
    """One decoded message; payload fields are also attributes."""
    op: int
    name: str
    fields: dict = field(default_factory=dict)
    extra: int = 0

    def __getattr__(self, key):
        try:
            return self.__dict__["fields"][key]
        except KeyError:
            raise AttributeError(key) from None


class Reader:
    """Cursor over one payload."""

    def __init__(self, payload):
        self.buf = memoryview(payload)
        self.pos = 0

    def remaining(self):
        return len(self.buf) - self.pos

    def _take(self, n):
        if n < 0 or self.pos + n > len(self.buf):
            raise ProtocolError("payload shorter than its specification")
        start = self.pos
        self.pos += n
        return start

    def i4(self):
        return struct.unpack_from("=i", self.buf, self._take(4))[0]

    def r4(self):
        return struct.unpack_from("=f", self.buf, self._take(4))[0]

    def r8(self):
        return struct.unpack_from("=d", self.buf, self._take(8))[0]

    def str(self):
        n = self.i4()
        start = self._take(n)
        return bytes(self.buf[start:start + n]).decode("latin-1")

    def array(self, kind, count):
        dtype = _DTYPES[kind]
        start = self._take(count * dtype.itemsize)
        return np.frombuffer(self.buf, dtype=dtype, count=count, offset=start)


def _count(expr, values):
    n = 1
    for name in expr.split("*"):
        n *= int(name) if name.isdigit() else int(values[name])
    return n


def _decode_catalog(rd):
    categories = []
    for _ in range(rd.i4()):
        name = rd.str()
        entries = []
        for _ in range(rd.i4()):
            entries.append((rd.str(), rd.str(), rd.i4()))
        categories.append((name, entries))
    return {"categories": categories}


def decode(op, payload):
    """Decode one payload into a Message (unknown opcodes keep their size)."""
    if op not in SPECS:
        return Message(op, "UNKNOWN", {"nbytes": len(payload)})
    rd = Reader(payload)
    if FIELDS[op] is None:
        values = _decode_catalog(rd)
    else:
        values = {}
        for name, kind, count in FIELDS[op]:
            if count is None:
                values[name] = getattr(rd, kind)()
            elif kind == "str":
                values[name] = [rd.str() for _ in range(_count(count, values))]
            else:
                values[name] = rd.array(kind, _count(count, values))
    msg = Message(op, NAMES[op], values, rd.remaining())
    if op == 1:
        if msg.magic != MAGIC:
            raise ProtocolError("byte-order mismatch in HELLO")
        if msg.version != PROTOCOL_VERSION:
            raise ProtocolError(f"protocol version {msg.version}, "
                                f"expected {PROTOCOL_VERSION}")
    return msg


def _read_exact(stream, n):
    data = b""
    while len(data) < n:
        chunk = stream.read(n - len(data))
        if not chunk:
            break
        data += chunk
    return data


def read_messages(stream, record=None):
    """Yield (op, payload) from a binary stream until its end.

    A stream that ends between messages stops cleanly; one that ends
    inside a message raises ProtocolEOF. With record, the raw bytes are
    also written to that binary file object.
    """
    while True:
        header = _read_exact(stream, 8)
        if not header:
            return
        if len(header) < 8:
            raise ProtocolEOF("stream ended inside a message header")
        op, nbytes = struct.unpack("=ii", header)
        if nbytes < 0:
            raise ProtocolError(f"negative payload length for opcode {op}")
        payload = _read_exact(stream, nbytes)
        if len(payload) < nbytes:
            raise ProtocolEOF(f"stream ended inside opcode {op}")
        if record is not None:
            record.write(header)
            record.write(payload)
        yield op, payload
