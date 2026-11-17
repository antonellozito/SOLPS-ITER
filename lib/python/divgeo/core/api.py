"""Prototypes of the functions of libdivgeo used from Python: the core of
DivGeo (unchanged C) and the C part of the Python interface (src/py).

Pointers to core structures are plain addresses (c_void_p); strings of the
core are bytes in Latin-1."""

import ctypes

P = ctypes.c_void_p
I = ctypes.c_int
D = ctypes.c_double
S = ctypes.c_char_p
SIZE = ctypes.c_size_t
PI = ctypes.POINTER(ctypes.c_int)
PD = ctypes.POINTER(ctypes.c_double)
PP = ctypes.POINTER(ctypes.c_void_p)
PS = ctypes.POINTER(ctypes.c_char_p)
PSIZE = ctypes.POINTER(ctypes.c_size_t)

# Called after the records of messages, notifications, flushes and the end
# of a view (argument: the View)
EVENTPROC = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

# Called at the end of ConfigureXApp (argument: the XApp)
CONFIGUREPROC = ctypes.CFUNCTYPE(None, ctypes.c_void_p)

# Entries of the Variables menu: (menu, kind, object, label)
VARSMENUPROC = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int,
                                ctypes.c_void_p, ctypes.c_char_p)

# Message boxes of the commands: (View, kind, text) -> 0 for OK
BOXPROC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
                           ctypes.c_char_p)

PROTOTYPES = {
    # XApp and documents (xapp.c, app.c, dgfile.c)
    "CreateXApp": (P, [PI, PS]),
    "FreeXApp": (P, [P]),
    "XAppStr": (P, [P, I]),
    "AddApp": (P, [P]),
    "LoadNormalApp": (P, [P, S, PP, PI]),
    "FreeApp": (P, [P]),
    "FreeUndoInfo": (None, [P]),
    "SaveApp": (I, [P, S, I]),
    "Undo": (None, [P]),
    "Redo": (None, [P]),
    "Cancel": (None, [P]),
    "GlueNormals": (I, [P, P, P]),
    "UndoMark": (None, [P]),
    "Free": (P, [P]),
    "GetShortFName": (P, [S]),
    "ExpandFilename": (P, [S]),
    "DetectFileType": (I, [S]),
    "SetAppFName": (None, [P, S]),
    "IsAppUnsaved": (I, [P]),
    "FreeView": (P, [P]),
    # Views (view.c)
    "SetViewApp": (None, [P, P]),
    "SetActiveView": (None, [P]),
    "RepaintView": (None, [P]),
    "CallToolProc": (None, [P, P, I, I, I]),
    "SetViewFactor": (None, [P, D, D, D, D]),
    "ScreenRotate": (None, [P, I, PD, PD]),
    "ScreenX": (I, [P, D]),
    "ScreenY": (I, [P, D]),
    # Python interface (src/py)
    "CreatePyView": (P, [P, I]),
    "SetPyViewRealized": (None, [P, I]),
    "SetPyViewSquares": (None, [P, I]),
    "SetPyViewSize": (None, [P, I, I]),
    "ResizePyView": (None, [P, I, I]),
    "SetPyEventProc": (None, [EVENTPROC]),
    "TakePyRecs": (SIZE, [PP, PP, PSIZE]),
    "ResetPyRecs": (None, []),
    "SetPyXAppConfig": (None, [S, I, ctypes.c_ulong]),
    "GetPyMsgCount": (I, []),
    "GetPyMsgId": (I, [I]),
    "GetPyMsgName": (S, [I]),
    "SetPyMsgValue": (None, [I, S]),
    "SetPyConfigureProc": (None, [CONFIGUREPROC]),
    "GetPyHelpFileName": (P, [P]),
    "GetPyVersion": (I, []),
    "GetPyVersionStr": (P, [I]),
    "GetPyGroupCount": (I, [P]),
    "GetPyLayout": (SIZE, [I, PS, PSIZE]),
    "GetPyLayoutType": (ctypes.c_char, [I]),
    "GetPyRecSize": (SIZE, []),
    "PyViewMsgVersion": (None, [P]),
    "PyFatalError": (None, [S]),
    "PyFatalError2": (None, [S, S, S]),
    "PyNotifyView": (None, [P, I, P]),
    # Commands (src/py/py_cmds.c)
    "SetPyBoxProc": (None, [BOXPROC]),
    "PyCbCmDelObjects": (None, [P, I]),
    "PyCbChangeFlags": (None, [P, ctypes.c_ulong]),
    "PyCbCmShowInvalidVars": (I, [P]),
    "PyCbAddVarSet": (P, [P, P]),
    "PyCbDelVarSet": (None, [P, P]),
    "PyVarsMenu": (I, [P, VARSMENUPROC]),
    "PyDwUndoButton": (I, [P, I]),
    "PyDwIfExists": (I, [P, I]),
    "PyDwIfNotExists": (I, [P, I]),
    "PyDwShowFlags": (I, [P, I]),
    "PyDwRebuildCarreInfo": (I, [P]),
    "PyViewMsg": (None, [P, S]),
    "PyViewMsgId": (None, [P, I]),
    "PyGetStr": (P, [P, I]),
    "PyMeshUnsaved": (I, [P]),
    "PyVarFromVarSetDef": (I, [P]),
    "PyVarIsLayerIndex": (I, [P]),
    "PyAutosave": (I, [P]),
}
for _name in ("PyCbUndo", "PyCbRedo", "PyCbRedoAll", "PyCbMarkAll",
              "PyCbMarkAllChords", "PyCbUnmarkAll", "PyCbCmRemoveSeparators",
              "PyCbViewRefresh", "PyCbZoomIn", "PyCbZoomOut",
              "PyCbShowPicture", "PyCbShowSelection", "PyCbIncAngle",
              "PyCbDecAngle", "PyCbResetAngle", "PyCbStretchX",
              "PyCbStretchY", "PyCbShrinkX", "PyCbShrinkY",
              "PyCbResetAspectRatio", "PyCmPrevZoom", "PyCmRemoveLabels",
              "PyCbCmAppendTemplate", "PyCmConvertElemsToChords",
              "PyCmConvertChordsToElems", "PyCbCmRenumber", "PyCbCmExtChords",
              "PyCmRebuildCarreInfo"):
    PROTOTYPES[_name] = (None, [P])

# The tools of the three slots, in the order of the tool menus
TOOLS = ("TlZoom", "TlMark", "TlExamine", "TlRotate", "TlStretch",
         "TlMoveObject", "TlRemoveObject", "TlAddElem", "TlAddSource",
         "TlAddChord", "TlAddSurface", "TlAddGridPoint", "TlMoveMeshPoint",
         "TlSplitElem", "TlJoinElems", "TlConnectPoints", "TlRepositionElem",
         "TlMirrorNormals", "TlExtChord", "TlAdjustChord")


def declare(dll):
    for name, (restype, argtypes) in PROTOTYPES.items():
        f = getattr(dll, name)
        f.restype = restype
        f.argtypes = argtypes


# Constants of the core headers (view.h, dgfile.h)
TL_PRESS, TL_MOTION, TL_ENTER, TL_LEAVE, TL_RELEASE, TL_CANCEL, TL_DBLCLK = (
    3, 4, 5, 6, 7, 8, 9)
N_ADD, N_ADDED, N_CHANGE, N_CHANGED, N_DEL, N_DELETED = (
    0x0001, 0x0002, 0x0004, 0x0008, 0x0010, 0x0020)
N_ALT, N_NEWAPP, N_MARK, N_DESTROYVIEW, N_EXAMINE = (
    0x0040, 0x0080, 0x0100, 0x0200, 0x0400)
N_RECENTFILES, N_NEWTOOL, N_NOW, N_USER = 0x1000, 0x2000, 0x4000, 0x8000
UPDATE_MAX, UPDATE_INCR = 1000, 100
DGFM_APP, DGFM_CONFIG, DGFM_TMP = 1, 2, 3
# Error codes (msg.h)
ERR_FWRITE, ERR_NOPREFS, ERR_NOCONFIG = 22, 75, 31
