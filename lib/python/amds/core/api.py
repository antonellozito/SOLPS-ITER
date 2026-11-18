"""Prototypes of the functions of libamds used from Python: the core of
AMDS (unchanged C) and the C part of the Python interface (src/py).

Pointers to core structures are plain addresses (c_void_p); strings of the
core are bytes in Latin-1."""

import ctypes

P = ctypes.c_void_p
I = ctypes.c_int
S = ctypes.c_char_p
SIZE = ctypes.c_size_t
PI = ctypes.POINTER(ctypes.c_int)
PS = ctypes.POINTER(ctypes.c_char_p)
PSIZE = ctypes.POINTER(ctypes.c_size_t)

# Callbacks of py_api.c: notifications (view, message, object), a view
# freed or asking for Unsaved work (view), the end (exit code); list items
NOTIFYPROC = ctypes.CFUNCTYPE(None, P, I, P)
VIEWPROC = ctypes.CFUNCTYPE(None, P)
EXITPROC = ctypes.CFUNCTYPE(None, I)
ITEMPROC = ctypes.CFUNCTYPE(None, S)
# py_graph.c: the calls of a graph view (dialog, op, i, a, b, c, d, text)
# and the text extents (dialog, text, width, height)
D = ctypes.c_double
PD = ctypes.POINTER(ctypes.c_double)
GRAPHPROC = ctypes.CFUNCTYPE(None, I, I, I, D, D, D, D, S)
GRAPHTEXTPROC = ctypes.CFUNCTYPE(None, I, S, PD, PD)

PROTOTYPES = {
    # py_api.c
    "GetPyLayout": (SIZE, [I, PS, PSIZE]),
    "GetPyLayoutType": (ctypes.c_char, [I]),
    "PyGroupCount": (I, [P]),
    "PyCreateGroup": (P, []),
    "PyFreeGroup": (P, [P]),
    "PyDocReaction": (P, [P, I]),
    "PyDocEnabled": (P, [P, I]),
    "PyReactionActive": (I, [P, P]),
    "PyIsStartupParticle": (I, [P, P]),
    "PyUndo": (None, [P]),
    "PyRedo": (None, [P]),
    "PyCancel": (None, [P]),
    "PyVarDefName": (S, [P]),
    "PyVarDefDescr": (S, [P]),
    "SetPyProcs": (None, [NOTIFYPROC, VIEWPROC, VIEWPROC, EXITPROC]),
    "PyCreateXApp": (P, [PI, PS]),
    "PyCreateView": (P, [P, P, P, I, I, I, I, I]),
    "PyFreeView": (None, [P]),
    "PyCloseView": (None, [P, I]),
    # py_cmds.c
    "PyGetSelectedReactions": (P, [P, PI, I]),
    "PyViewListItems": (None, [P, ITEMPROC]),
    "PyParticleEntrySensitive": (I, [P, P, I, I, I]),
    "PyForbidEntrySensitive": (I, [P, P, I]),
    "PyTypeEntrySensitive": (I, [P, P]),
    "PyCbRestrictInput": (None, [P, P, I]),
    "PyCbRestrictOutput": (None, [P, P, I]),
    "PyCbForbidParticle": (None, [P, P, I]),
    "PyCbRestrictType": (None, [P, P]),
    "PyCbEditRedoAll": (None, [P]),
    "PyCbActivate": (None, [P, PI, I]),
    "PyCbDeactivate": (None, [P, PI, I]),
    "PyCbCut": (None, [P, PI, I]),
    "PyCbCopy": (None, [P, PI, I]),
    "PyCbCrop": (None, [P, PI, I]),
    "PyCbPasteOr": (None, [P]),
    "PyNewSubsetDoc": (P, [P]),
    "PyCloneSubsetDoc": (P, [P]),
    "PyNewViewDoc": (P, [P]),
    "PyCbFileQuit": (None, [P]),
    "PyAltReactionName": (S, [P]),
    "PyGotoIndex": (I, [P, P]),
    # py_graph.c
    "SetPyGraphProcs": (None, [GRAPHPROC, GRAPHTEXTPROC]),
    "PyCreateGraph": (P, [P, I]),
    "PyGraphRealize": (None, [P]),
    "PyGraphResize": (None, [P, I, I]),
    "PyGraphExpose": (None, [P]),
    "PyGraphRepaint": (None, [P]),
    "PyGraphCalcDone": (None, [P, S]),
    "PyGraphUpdate": (P, [P, D, D, D, D, PD, P]),
    "PyGraphFit": (None, [P, ctypes.POINTER(ctypes.c_char),
                         ctypes.POINTER(ctypes.c_char)]),
    "PyGraphPsCreate": (P, [P, D, D, D, I]),
    "PyGraphPsOutput": (I, [P, S, I]),
    "PyGraphPsFree": (None, [P]),
    "PyGraphFree": (None, [P]),
    # the core
    "GetParticleVar": (S, [P, P, P, P]),
    "SetParticleVar": (None, [P, P, P, P, S]),
    "GetActiveReactions": (P, [P]),
    "ValidateReactions": (P, [P, P]),
    "SetStartupParticle": (None, [P, P, I]),
    "AddVarDef": (P, [P, S]),
    "ChangeVarDef": (I, [P, P, I, I]),
    "SetVarDefStr": (I, [P, P, S, S]),
    "DelVarDef": (P, [P, P]),
    "GetVar2": (S, [P, S, S]),
    "CreateDatabase": (P, [S]),
    "CreateDoc": (P, [P]),
    "FreeDoc": (P, [P]),
    "LoadDoc": (I, [P, S]),
    "SaveDoc": (I, [P, S]),
    "OutputDoc": (I, [P, S]),
    "UpdateVarDefs": (None, [P, P]),
    "UndoMark": (None, [P]),
    "FreeUndoInfo": (None, [P]),
    "IsSubclassedParticle": (I, [P, P, I]),
    "GetReactionDatabase": (S, [P]),
    "GetReactionSection": (S, [P]),
    "GetReactionNumber": (S, [P]),
    "GetShortFName": (S, [S]),
    "GroupAt": (P, [P, SIZE]),
    "InGroup": (I, [P, P]),
}


def declare(dll):
    for name, (restype, argtypes) in PROTOTYPES.items():
        f = getattr(dll, name)
        f.restype = restype
        f.argtypes = argtypes


# Variable definitions (amvars.h)
VDT_STRING, VDT_INT, VDT_FLOAT = 1, 2, 3
VDF_REACTIONS, VDF_PARTICLES, VDF_NOEXPORT = 0x0001, 0x0002, 0x0004
VDFM_APPLY = VDF_REACTIONS | VDF_PARTICLES

# Notifications (amview.h)
N_ALT, N_NOW, N_SEL, N_SETVAR = 0x0001, 0x0002, 0x0004, 0x0008
N_VARDEFS, N_DEL, N_ENABLE = 0x0010, 0x0020, 0x0040
