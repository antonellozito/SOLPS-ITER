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
PL = ctypes.POINTER(ctypes.c_long)

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

# Items of the zone menus of the dialogs: (label, zone)
ITEMPROC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int)

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
    "RealX": (D, [P, I]),
    "RealY": (D, [P, I]),
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
    "PyCbFileOutput": (None, [P, S, S, S]),
    # Dialogs (src/py/py_dlgs.c)
    "PyRotMoveRotate": (P, [P, I, I]),
    "PyRotMoveMove": (P, [P, D, D, D, I, I]),
    "PyStretchDlgSet": (None, [P, D, D]),
    "PyCreateNode": (P, [P, D, D]),
    "PyCreateSource": (P, [P, D, D]),
    "PyCreateChord": (P, [P, I, D, D, D, D, D, D]),
    "PyCreateSurfaceByLevel": (P, [P, I, D]),
    "PyCreateSurfaceByXY": (P, [P, D, D]),
    "PyDelSurfacesOfCreator": (I, [P, S]),
    "PyExaminedSurfaceEx": (I, [P, PI, PD, PP]),
    "PyExaminedGridPointEx": (I, [P, PP]),
    "PyMarkBoundingElem": (None, [P, I]),
    "PySurfaceZoneItems": (I, [P, ITEMPROC]),
    "PyGridPointSegItems": (I, [P, ITEMPROC]),
    "PyCreateGridPoint": (P, [P, I, D]),
    "PyDelGridPointsOfZone": (None, [P, I]),
    "PyExportElemsCheck": (I, [P, P]),
    "PyAppFileName": (P, [P, I]),
    "PyInfoCounts": (None, [P, ctypes.POINTER(ctypes.c_uint)]),
    "PyMeshOptions": (None, [P, PI, PD, PI]),
    "PyMeshHeader": (P, [P]),
    # Core calls of the dialogs
    "GlueNodes": (I, [P, P, D, PI]),
    "GlueElems": (I, [P, P, D, D, I, PI]),
    "SetViewAngle": (None, [P, D]),
    "SetViewFlags": (None, [P, ctypes.c_ulong]),
    "ValidatePtr": (None, [P, S]),
    "DistributeLaw": (D, [D, I, D, D, I]),
    "DistributeSurfaces": (I, [P, I, I, D, D, I, D, D, I, PP]),
    "DistributeGridPoints": (I, [P, I, I, D, D, I, I]),
    "ParseSurfaceCreatorId": (I, [P, PI, PI, PD, PD, PI, PD, PD, PI]),
    "ParseGridPointCreatorId": (I, [P, PI, PI, PD, PD, PI, PI]),
    "GetSurfacesStatsStr": (P, [P]),
    "GetGridPointStatsStr": (P, [P]),
    "GetVersionStr": (P, [I]),
    "CheckMeshHeaderString": (I, [P, S]),
    "SetMeshHeaderString": (None, [P, S]),
    "AddEquil": (I, [P, S]),
    "AddTemplate": (I, [P, S, D, D, D, D]),
    "LoadMesh": (I, [P, S]),
    "SaveMesh": (I, [P, S]),
    "LoadTopology": (I, [P, S, I]),
    "WriteElemsAsDgTemplate": (I, [P, S]),
    "CreatePsView": (P, [P, D, D, D]),
    "ShowPicture": (None, [P]),
    "PsViewOutput": (I, [P, S, I, S]),
    "SetOutputFlags": (None, [P, ctypes.c_long]),
    "SetAppOutputMode": (None, [P, I]),
    "SetMeshSlidingThreshold": (None, [P, D]),
    "SetDoubleMeshBorderFlag": (None, [P, I]),
    "SetMeshSlidingMode": (None, [P, I]),
    "IsLocked": (I, [P]),
    "WhyLocked": (P, [P, P]),
    # Variables and setup (src/py/py_vars.c)
    "PyGroupList": (I, [P, PP, I]),
    "PyVarValueKind": (I, [P]),
    "PyVarValueDescr": (P, [P, P, P]),
    "PyAcceptVarsField": (I, [P, P, P, S]),
    "PyVarsCompare": (I, [P, P, P, I, S]),
    "PyVarsDisplay": (None, [P, P, P]),
    "PyInvalidVarsItems": (I, [P, ITEMPROC]),
    "PyInvalidVarsWhere": (P, [P, I, PI]),
    "PyAppHasGeometry": (I, [P]),
    "PyConfigFileName": (None, [P, P]),
    "PySaveConfig": (I, [P, S]),
    "PyOtherApps": (I, [P]),
    "PyUpdateOtherApps": (None, [P]),
    # Topology (src/py/py_topo.c)
    "PyTopoDetect": (None, [P, I]),
    "PyTopoExamined": (I, [P, P, PD, PI, PP, PP, PL]),
    "PyTopoXptLevel": (P, [P, P, D]),
    "PyTopoXSeg": (P, [P, P, I, S, S, I, I]),
    "PyTopoXSegRevert": (P, [P, P]),
    "PyTopoSZSet": (P, [P, P, I, I, I, I, I, I, S, S]),
    "PyTopoSZDelete": (P, [P, P]),
    "PyTopoZoneItems": (I, [P, ITEMPROC]),
    "PyTopoZoneInfo": (None, [P, PI, PP, PP, PI, PI, PI, PL]),
    # Core calls of the variables, setup and topology dialogs
    "GetVarEx": (P, [P, P, P]),
    "GetVar": (P, [P, P, P]),
    "SetVar": (I, [P, P, P, P, S]),
    "GetObjDescription": (P, [P, P]),
    "WhyLockedEx": (P, [P, P, P]),
    "MarkGroup": (None, [P, P, I]),
    "GroupAt": (P, [P, SIZE]),
    "CheckAllVars": (I, [P, P]),
    "AddVarSetDef": (P, [P, S, S, I, I]),
    "ChangeVarSetDef": (None, [P, P, S, S, I, I, P]),
    "DelVarSetDef": (P, [P, P]),
    "AddVarDef": (P, [P, P, S, S, I, I, I, I]),
    "ChangeVarDef": (I, [P, P, P, S, S, I, I, I, I]),
    "DelVarDef": (P, [P, P]),
    "ChangeHelpString": (None, [P, P, S]),
    "GetTopologyName": (P, [P]),
    "SetTopologyName": (None, [P, S]),
    "SetViewEditTopology": (None, [P, I]),
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


# functions that a library built before them lacks (the Python
# rasterizer is used then)
OPTIONAL = {
    "PyRasterDraw": (ctypes.c_long, [P, I, I, P, ctypes.c_long,
                                     ctypes.c_long, I, I, I, I, I, I,
                                     ctypes.c_uint, P, P, P, P, I, P, P, P,
                                     I, I, I, I]),
    "PyRasterElemLines": (ctypes.c_long, [P, ctypes.c_long, ctypes.c_long,
                                          I, I, I, I, P, ctypes.c_long]),
    "PyRasterAverage": (None, [P, I, I, I, P]),
    "PySetViewStep": (None, [P, D, D, D, D]),
    "PyElemSegments": (ctypes.c_long, [P, P, ctypes.c_long]),
}


def declare(dll):
    for name, (restype, argtypes) in PROTOTYPES.items():
        f = getattr(dll, name)
        f.restype = restype
        f.argtypes = argtypes
    for name, (restype, argtypes) in OPTIONAL.items():
        try:
            f = getattr(dll, name)
        except AttributeError:
            continue
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
# Object types (dg.h), show flags (view.h), laws of the distributions,
# output modes and flags, mesh sliding modes (sonnet.h, mesh.h)
T_ELEM, T_NODE, T_EQUIL, T_TEMPLATE, T_SONNET = 1, 2, 3, 7, 18
T_SOURCE, T_CHORD, T_MESH, T_GRIDPOINTEX, T_SURFACEEX = 21, 22, 26, 32, 34
SHW_ELEMS, SHW_NODES, SHW_IRRNODES, SHW_TEMPLATE = 0x4, 0x20, 0x40, 0x80
SHW_EQUIL, SHW_SURFACES, SHW_GRIDPOINTS, SHW_MESH = 0x100, 0x200, 0x400, \
    0x1000
SHW_SOURCES, SHW_CHORDS = 0x4000, 0x8000
DGLAW_NORMAL, DGLAW_FLIPPED, DGLAW_2ALPHA, DGLAW_SYMMETRIC, DGLAW_DELTA = (
    0, 1, 2, 3, 4)
OUTPUTMODE_SONNET, OUTPUTMODE_CARRE, OUTPUTMODE_GOAT = 1, 2, 3
OF_NC_VARS, OF_NC_STRUCTURE, OF_NC_TARGETS, OF_NC_SURFACES, OF_NC_GPOINTS = (
    0x1, 0x2, 0x4, 0x8, 0x10)
MSMF_USE_SPLINE, MSMF_USE_SURFACE, MSMF_USE_POINTS = 0x1, 0x2, 0x4
MSM_SURFACE = MSMF_USE_SURFACE
MSM_SPLINE = MSMF_USE_SPLINE | MSMF_USE_POINTS
DG_VERSION = 21110
T_VARSET, T_XPOINTTEST, T_XPOINTSEG = 10, 23, 24
# Variable flags and types (vars.h)
VF_NOEXPORT, VF_FORELEMS, VF_FORSEPARATORS, VF_FORSOURCES, VF_FORCHORDS, \
    VF_LAYERINDEX = 0x1, 0x2, 0x4, 0x8, 0x10, 0x20
VFM_MULTIPLE = VF_FORELEMS | VF_FORSEPARATORS | VF_FORSOURCES | VF_FORCHORDS
VTF_HASELEMS, VTF_LOCKGROUP, VTF_SINGLE, VTF_STRUCTPART = (0x100, 0x200,
                                                          0x400, 0x800)
VTF_HASCHORDS, VTF_HAS_MESH_OBJECTS, VTF_TARGET, VTF_FILENAME = (
    0x1000, 0x2000, 0x4000, 0x8000)
VTM_HASGROUP = VTF_HASELEMS | VTF_HASCHORDS | VTF_HAS_MESH_OBJECTS
VT_INT, VT_FLOAT, VT_TEXT = 0x00, 0x01, 0x02
VT_FILENAME = 0x03 | VTF_FILENAME
VT_ELEM = 0x04 | VTF_HASELEMS | VTF_LOCKGROUP
VT_ELEMS = 0x05 | VTF_HASELEMS | VTF_LOCKGROUP
VT_TARGET1 = 0x06 | VTF_HASELEMS | VTF_LOCKGROUP | VTF_TARGET
VT_TARGET2 = 0x07 | VTF_HASELEMS | VTF_LOCKGROUP | VTF_TARGET
VT_STRUCTURE = 0x08 | VTF_HASELEMS | VTF_LOCKGROUP | VTF_SINGLE
VT_STRUCTPART = 0x09 | VTF_HASELEMS | VTF_LOCKGROUP | VTF_STRUCTPART
VT_CHORDS = 0x0A | VTF_HASCHORDS
VT_MESH_CELLS = 0x0B | VTF_HAS_MESH_OBJECTS
VT_MESH_ELEMENTS = 0x0C | VTF_HAS_MESH_OBJECTS
VT_MESH_H_ELEMENTS = 0x0D | VTF_HAS_MESH_OBJECTS
VT_MESH_V_ELEMENTS = 0x0E | VTF_HAS_MESH_OBJECTS
VT_TOPVIEW = 0x0F | VTF_HASELEMS
GPSF_USED, GPSF_TARGET_CW = 0x1, 0x2
# Message ids (msg.h)
ERR_INVNUMBERS, ERR_NOSONNET, ERR_NOTHINGTODO, ERR_INVAREA = 16, 30, 32, 34
ERR_CARRE_INHIBITS, ERR_NOSURFZONE, ERR_NO_MARKED_ELEMS = 83, 112, 90
ERR_BAD_OBJECT_TYPE, ERR_BADMASK, ERR_PSVIEWSIZE = 103, 65, 70
ERR_PIPECREATE, ERR_FORK = 68, 69
ERR_USEDBY, ERR_MINMAXVARSETS, ERR_BADNAME, ERR_DUPNAME = 9, 17, 18, 19
ERR_SINGLE, ERR_MULTGROUP, STR_VARSLOST = 27, 29, 2021
QUE_WITHGEOMETRY, QUE_UPDATEAPPS = 4000, 4001
ENV_VARSFILESETMASK = 6012
MSG_TEMPLATELOADED, MSG_EQUILLOADED, MSG_SONNETLOADED = 1004, 1006, 1011
MSG_FILEPRINTED = 1033
ENV_EQUILMASK, ENV_TEMPLATEMASK, ENV_SONNETMASK = 6003, 6004, 6005
ENV_EQUILMASK2, ENV_TEMPLATEMASK2, ENV_SONNETMASK2 = 6009, 6010, 6011
# Error codes (msg.h)
ERR_FWRITE, ERR_NOPREFS, ERR_NOCONFIG = 22, 75, 31
