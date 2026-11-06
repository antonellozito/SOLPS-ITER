"""A plot with all its settings, drawn again elsewhere (export shapes and
the page composer)."""

from dataclasses import dataclass, replace

from .canvas import Plot2D
from .styles import LabelStyle, PlotStyle


@dataclass
class Snapshot:
    """One plot with all its settings, drawn again by render_snapshot
    (export shapes and the page composer)."""
    run: object
    data: object
    style: PlotStyle
    unit: str = None
    overlays: dict = None
    layers: dict = None
    view: tuple = None
    labels: LabelStyle = None
    title: str = ""             # automatic title
    values: dict = None         # ${NAME} of the label texts


def render_snapshot(fig, snap, rect=(0.0, 0.0, 1.0, 1.0), header=True):
    """Draw a Snapshot in a rectangle of a figure (figure fraction)."""
    p = Plot2D(fig, rect)
    if snap.layers:
        p.layer_styles = {k: replace(s) for k, s in snap.layers.items()}
    p.set_run(snap.run, hover=False)
    ls = snap.labels or LabelStyle()
    p.set_labels(ls, snap.title, snap.values, header)
    if snap.view:
        p.set_view(snap.view)
    p.show(snap.data, snap.style, snap.unit, snap.overlays)
    p.set_labels(ls, snap.title, snap.values, header)
    if snap.view:
        p.set_view(snap.view)
    return p
