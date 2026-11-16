"""Resources of the drawing area and the drawing modes of the view, as the
Motif view reads and uses them (x_view.c: viewExtRes, viewCfgRes,
SetXmViewMode).

The resources are read with the widget path of the drawing area (shell
DivGeo, main window main, drawing area draw)."""

from ..core import resources

PATH_NAMES = ["DivGeo", "main", "draw"]
PATH_CLASSES = ["DivGeo", "XmMainWindow", "XmDrawingArea"]

# viewExtRes: (field, resource name, class, default)
COLORS = (
    ("pxBackground", "background", "Background", "RGBi: 0/0/0"),
    ("pxHighlight", "highlightColor", "HighlightColor", "RGBi: 1/1/1"),
    ("pxErrorHighlight", "errorHighlightColor", "ErrorHighlightColor",
     "RGBi: 1/1/1"),
    ("pxNode", "nodeColor", "NodeColor", "RGBi: .5/.5/.5"),
    ("pxElem", "elemColor", "ElemColor", "RGBi: .5/.5/.5"),
    ("pxSurface", "surfaceColor", "SurfaceColor", "RGBi: .5/.5/.5"),
    ("pxHighlightRect", "highlightRectColor", "HighlightRectColor",
     "RGBi: 1/1/1"),
    ("pxTemplate", "templateColor", "TemplateColor", "RGBi: .3/.3/.3"),
    ("pxNormal", "normalColor", "NormalColor", "RGBi: .5/.5/.5"),
    ("pxMark", "markColor", "MarkColor", "RGBi: .5/.5/.5"),
    ("pxXPoint", "xPointColor", "XPointColor", "RGBi: .7/.7/.7"),
    ("pxEquil1", "equilColor1", "EquilColor1", "RGBi: .1/.1/.1"),
    ("pxEquil2", "equilColor2", "EquilColor2", "RGBi: .2/.2/.2"),
    ("pxAxes", "axesColor", "AxesColor", "RGBi: .3/.3/.3"),
    ("pxGrid", "gridColor", "GridColor", "RGBi: .2/.2/.2"),
    ("pxGridText", "gridTextColor", "GridTextColor", "RGBi: .3/.3/.3"),
    ("pxElemNumber", "elemNumberColor", "ElemNumberColor", "RGBi: .3/.3/.3"),
    ("pxViewLabel", "viewLabelColor", "ViewLabelColor", "RGBi: .9/.9/.9"),
    ("pxSonnet", "sonnetDataColor", "SonnetDataColor", "RGBi: .3/.3/.3"),
    ("pxGridPoint", "gridPointColor", "GridPointColor", "RGBi: .7/.7/.7"),
    ("pxSeparator", "separatorColor", "SeparatorColor", "RGBi: .7/.7/.7"),
    ("pxSource", "sourceColor", "SourceColor", "RGBi: .7/.7/.7"),
    ("pxChord", "chordColor", "ChordColor", "RGBi: .7/.7/.7"),
    ("pxXPointTest1", "xpoint1Color", "XPointColor", "RGBi: .7/.7/.7"),
    ("pxXPointTest2", "xpoint2Color", "XPointColor", "RGBi: .7/.7/.7"),
    ("pxXPointSeg", "xpointSegColor", "XPointColor", "RGBi: .7/.7/.7"),
    ("pxMeshElement1", "meshElementColor1", "MeshElementColor1",
     "RGBi: 0.7/0.7/0.7"),
    ("pxMeshElement2", "meshElementColor2", "MeshElementColor2",
     "RGBi: 0.7/0.7/0.7"),
    ("pxMeshCellCenter1", "meshCellCenterColor1", "MeshCellCenterColor1",
     "RGBi: 0.7/0.7/0.7"),
    ("pxMeshCellCenter2", "meshCellCenterColor2", "MeshCellCenterColor2",
     "RGBi: 0.7/0.7/0.7"),
    ("pxTool[0]", "lToolColor", "LToolColor", "RGBi: .7/.7/.7"),
    ("pxTool[1]", "mToolColor", "MToolColor", "RGBi: .7/.7/.7"),
    ("pxTool[2]", "rToolColor", "RToolColor", "RGBi: .7/.7/.7"),
    ("pxTool[3]", "iToolColor", "IToolColor", "RGBi: 0/0/0"),
)

WIDTHS = (
    ("whHighlight", "highlightWidth", "HighlightWidth", 0),
    ("whNode", "nodeWidth", "Width", 1),
    ("whElem", "elemWidth", "Width", 1),
    ("whSurface", "surfaceWidth", "Width", 1),
    ("whHighlightRect", "highlightRectWidth", "HighlightWidth", 0),
    ("whTemplate", "templateWidth", "Width", 1),
    ("whNormal", "normalWidth", "Width", 1),
    ("whMark", "markWidth", "MarkWidth", 5),
    ("whXPoint", "xPointWidth", "Width", 1),
    ("whEquil", "equilWidth", "Width", 1),
    ("whAxes", "axesWidth", "Width", 1),
    ("whGrid", "gridWidth", "Width", 1),
    ("whGridText", "gridTextWidth", "Width", 1),
    ("whElemNumber", "elemNumberWidth", "Width", 1),
    ("whViewLabel", "viewLabelWidth", "Width", 1),
    ("whSonnet", "sonnetDataWidth", "Width", 1),
    ("whGridPoint", "gridPointWidth", "Width", 1),
    ("whSeparator", "separatorWidth", "Width", 1),
    ("whSource", "sourceWidth", "Width", 1),
    ("whChord", "chordWidth", "Width", 1),
    ("whXPointTest1", "xpoint1Width", "Width", 1),
    ("whXPointTest2", "xpoint2Width", "Width", 1),
    ("whXPointSeg", "xpointSegWidth", "Width", 1),
    ("whMeshElement1", "meshElementWidth1", "Width", 1),
    ("whMeshElement2", "meshElementWidth2", "Width", 1),
    ("whMeshCellCenter1", "meshCellCenterWidth1", "Width", 1),
    ("whMeshCellCenter2", "meshCellCenterWidth2", "Width", 1),
)

INTS = (
    ("updateDelay", "updateDelay", "UpdateDelay", 1000),
    ("updateVarsDelay", "updateVarsDelay", "UpdateDelay", 1000),
    ("updateInfoDelay", "updateInfoDelay", "UpdateDelay", 1000),
    ("updateMouseDelay", "updateMouseDelay", "UpdateDelay", 1000),
    ("exposeDelay", "exposureDelay", "ExposureDelay", 300),
)

# viewCfgRes: (field of the View, resource name, class, default)
CONFIG = (
    ("nodeR", "nodeRadius", "Radius", 4),
    ("equilLen", "equilLen", "EquilLen", 10),
    ("minZoomX", "minZoomX", "MinZoomX", 20),
    ("minZoomY", "minZoomY", "MinZoomY", 20),
    ("normalLen", "normalLen", "NormalLen", 30),
    ("gridPointLen", "gridPointLen", "GridPointLen", 30),
    ("srcR", "sourceR", "SourceR", 20),
    ("arrowWidth", "arrowWidth", "ArrowWidth", 3),
    ("arrowLength", "arrowLength", "ArrowLength", 30),
    ("gridCellMax", "gridCellMax", "GridCellMax", 330),
    ("labelOffsetX", "labelOffsetX", "LabelOffsetX", 30),
    ("labelOffsetY", "labelOffsetY", "LabelOffsetY", 30),
    ("shpIncr", "showPictureIncr", "ShowPictureIncr", 5),
    ("meshCellCenterLen", "meshCellCenterLength", "MeshCellCenterLength", 3),
    ("meshPointRadius", "meshPointRadius", "MeshPointRadius", 3),
    ("gridPointSegEndLength", "separatrixSegEndLen", "SeparatrixSegEndLen",
     48),
)


def read_view_resources(db):
    """The resources of a drawing area: dict of the Motif field names
    (colours as 0xRRGGBB, widths, delays, bUseSquares, View config)."""
    def get(name, cls):
        return db.get(PATH_NAMES + [name], PATH_CLASSES + [cls])

    out = {}
    for field, name, cls, default in COLORS:
        value = get(name, cls)
        pixel = resources.to_pixel(value) if value is not None else None
        out[field] = (pixel if pixel is not None
                      else resources.to_pixel(default))
    for table in (WIDTHS, INTS, CONFIG):
        for field, name, cls, default in table:
            value = get(name, cls)
            number = resources.to_int(value) if value is not None else None
            out[field] = number if number is not None else default
    value = get("useSquares", "UseSquares")
    flag = resources.to_bool(value) if value is not None else None
    out["bUseSquares"] = 1 if flag else 0
    # the renderer of the Python interface (canvas.RENDERERS)
    value = (get("renderer", "Renderer") or "").strip().lower()
    out["renderer"] = (value if value in ("auto", "x", "hidpi", "smooth")
                       else "auto")
    return out


# The drawing modes (view.h) ##################################################

(VM1_NODE, VM0_NODE, VMX_NODE, VM1_ELEM, VM0_ELEM, VMX_ELEM, VM1_EQUIL,
 VM0_EQUIL, VMX_EQUIL, VM1_SURFACE, VM0_SURFACE, VMX_SURFACE,
 VM1_HIGHLIGHTRECT, VM0_HIGHLIGHTRECT, VMX_HIGHLIGHTRECT, VM2_EQUIL,
 VM1_TEMPLATE, VM0_TEMPLATE, VMX_TEMPLATE, VM1_ELEMNORMAL, VM0_ELEMNORMAL,
 VMX_ELEMNORMAL, VM1_ELEMMARK, VM0_ELEMMARK, VM1_XPOINT, VM0_XPOINT,
 VMX_XPOINT, VM1_GPOINT, VM0_GPOINT, VMX_GPOINT, VM1_AXES, VM1_GRID,
 VM1_GRIDTEXT, VM1_ELEMNUMBER, VM0_ELEMNUMBER, VM1_VIEWLABEL, VM0_VIEWLABEL,
 VM1_SONNETDATA, VM0_SONNETDATA, VM1_SEPARATOR, VM0_SEPARATOR, VMX_SEPARATOR,
 VM3_EQUIL, VM1_SOURCE, VM0_SOURCE, VMX_SOURCE, VM1_CHORD, VM0_CHORD,
 VMX_CHORD, VM1_XPOINTTEST, VM2_XPOINTTEST, VM0_XPOINTTEST, VMX_XPOINTTEST,
 VM1_XPOINTSEG, VM0_XPOINTSEG, VMX_XPOINTSEG, VM1_MESHELEMENT,
 VM0_MESHELEMENT, VMX_MESHELEMENT, VM2_MESHELEMENT, VM1_MESHCELLCENTER,
 VM2_MESHCELLCENTER, VM0_MESHCELLCENTER, VMX_MESHCELLCENTER, VMX2_MESHELEMENT,
 VMX12_MESHELEMENT) = range(66)

COPY, XOR = 0, 1

# XOR modes with the highlight colour (error highlight colour when the
# highlight mode of the App is off)
_XOR_HIGHLIGHT = (VMX_NODE, VMX_ELEM, VMX_EQUIL, VMX_SURFACE, VMX_TEMPLATE,
                  VMX_ELEMNORMAL, VMX_XPOINT, VMX_GPOINT, VMX_SEPARATOR,
                  VMX_SOURCE, VMX_CHORD, VMX_XPOINTTEST, VMX_XPOINTSEG,
                  VMX_MESHELEMENT, VMX_MESHCELLCENTER)

# Erase modes: background colour with the width of the object
_ERASE = {
    VM0_NODE: "whNode", VM0_ELEM: "whElem", VM0_EQUIL: "whEquil",
    VM0_HIGHLIGHTRECT: "whHighlightRect", VM0_SURFACE: "whSurface",
    VM0_TEMPLATE: "whTemplate", VM0_ELEMNORMAL: "whNormal",
    VM0_XPOINT: "whXPoint", VM0_ELEMMARK: "whMark",
    VM0_ELEMNUMBER: "whElemNumber", VM0_VIEWLABEL: "whViewLabel",
    VM0_SONNETDATA: "whSonnet", VM0_GPOINT: "whGridPoint",
    VM0_SEPARATOR: "whSeparator", VM0_SOURCE: "whSource",
    VM0_CHORD: "whChord", VM0_XPOINTSEG: "whXPointSeg",
}
_ERASE_MAX = {
    VM0_XPOINTTEST: ("whXPointTest1", "whXPointTest2"),
    VM0_MESHELEMENT: ("whMeshElement1", "whMeshElement2"),
    VM0_MESHCELLCENTER: ("whMeshCellCenter1", "whMeshCellCenter2"),
}

# Drawing modes: (colour, width)
_DRAW = {
    VM1_NODE: ("pxNode", "whNode"), VM1_ELEM: ("pxElem", "whElem"),
    VM1_EQUIL: ("pxEquil1", "whEquil"), VM2_EQUIL: ("pxEquil2", "whEquil"),
    VM3_EQUIL: ("pxXPoint", "whXPoint"),
    VM1_HIGHLIGHTRECT: ("pxHighlightRect", "whHighlightRect"),
    VM1_SURFACE: ("pxSurface", "whSurface"),
    VM1_TEMPLATE: ("pxTemplate", "whTemplate"),
    VM1_ELEMNORMAL: ("pxNormal", "whNormal"),
    VM1_XPOINT: ("pxXPoint", "whXPoint"), VM1_ELEMMARK: ("pxMark", "whMark"),
    VM1_AXES: ("pxAxes", "whAxes"), VM1_GRID: ("pxGrid", "whGrid"),
    VM1_GRIDTEXT: ("pxGridText", "whGridText"),
    VM1_ELEMNUMBER: ("pxElemNumber", "whElemNumber"),
    VM1_VIEWLABEL: ("pxViewLabel", "whViewLabel"),
    VM1_SONNETDATA: ("pxSonnet", "whSonnet"),
    VM1_GPOINT: ("pxGridPoint", "whGridPoint"),
    VM1_SEPARATOR: ("pxSeparator", "whSeparator"),
    VM1_SOURCE: ("pxSource", "whSource"), VM1_CHORD: ("pxChord", "whChord"),
    VM1_XPOINTTEST: ("pxXPointTest1", "whXPointTest1"),
    VM2_XPOINTTEST: ("pxXPointTest2", "whXPointTest2"),
    VM1_XPOINTSEG: ("pxXPointSeg", "whXPointSeg"),
    VM1_MESHELEMENT: ("pxMeshElement1", "whMeshElement1"),
    VM2_MESHELEMENT: ("pxMeshElement2", "whMeshElement2"),
    VM1_MESHCELLCENTER: ("pxMeshCellCenter1", "whMeshCellCenter1"),
    VM2_MESHCELLCENTER: ("pxMeshCellCenter2", "whMeshCellCenter2"),
}


def gc(res, mode, highlight_mode):
    """(function, foreground pixel, line width) of a mode, as the graphics
    context of the Motif view; None for an unknown mode (Motif stops with a
    fatal error before)."""
    bg = res["pxBackground"]
    hl = res["pxHighlight"] if highlight_mode else res["pxErrorHighlight"]
    if mode in _XOR_HIGHLIGHT:
        return XOR, bg ^ hl, res["whHighlight"]
    if mode == VMX12_MESHELEMENT:
        return XOR, bg ^ hl ^ res["pxMeshElement2"], res["whHighlight"]
    if mode == VMX2_MESHELEMENT:
        return XOR, bg ^ res["pxMeshElement2"], res["whMeshElement2"]
    if mode == VMX_HIGHLIGHTRECT:
        rect = (res["pxHighlightRect"] if highlight_mode
                else res["pxErrorHighlight"])
        return XOR, bg ^ rect, res["whHighlightRect"]
    if mode in _ERASE:
        return COPY, bg, res[_ERASE[mode]]
    if mode in _ERASE_MAX:
        a, b = _ERASE_MAX[mode]
        return COPY, bg, max(res[a], res[b])
    if mode in _DRAW:
        color, width = _DRAW[mode]
        return COPY, res[color], res[width]
    return None
