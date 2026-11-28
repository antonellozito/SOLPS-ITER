"""The vessel structures as the camera sees them (the background of its
images in the transparency mode): the real walls of the EIRENE wall (those
the rays of the camera stop on) and the structure of the run, turned all
around the axis, rendered off screen with the pinhole of the camera (its
position, the point it looks at, its roll and field of view), lit from the
camera."""

import numpy as np
import pyvista as pv

from . import meshes
from .scene import STRUCTURE, VESSEL
from ..tools import camera

PIXELS = 960                    # width of the rendering at least


def image(cam, geo, background, walls=()):
    """(height, width, 3) RGB (0 to 1) of the walls (segments R1, Z1, R2,
    Z2) and the structure (geo: the geometry of the 3D view,
    Data3D._build_geometry) seen by the camera cam, at least PIXELS wide,
    its pixels as those of the camera image (row 0 at the top) times an
    integer."""
    k = max(1, int(np.ceil(PIXELS / max(cam.nx, 1))))
    width, height = cam.nx * k, cam.ny * k
    o, f, _, up = camera.frame(cam)
    pl = pv.Plotter(off_screen=True, window_size=(width, height))
    try:
        pl.set_background(background)
        spec = dict(smooth_shading=True, split_sharp_edges=True,
                    specular=0.3, specular_power=12.0, ambient=0.25,
                    diffuse=0.75)
        full = (0.0, 2.0 * np.pi)
        seg = [np.reshape(s, (2, 2)) for s in np.asarray(
            walls, float).reshape(-1, 4)]
        for polys, closed in ((geo.get("solids", []), True),
                              (geo.get("walls", []), False), (seg, False)):
            m = meshes.surface(polys, *full, closed=closed)
            if m is not None and m.n_points:
                pl.add_mesh(m, color=STRUCTURE, **spec)
        m = meshes.surface(geo.get("vessel", []), *full, closed=True)
        if m is not None and m.n_points:    # its inside only: seen from in
            m = m.extract_surface().compute_normals(    # it, transparent
                auto_orient_normals=True)               # from outside
            pl.add_mesh(m, color=VESSEL, culling="front", **spec)
        pl.remove_all_lights()
        pl.add_light(pv.Light(light_type="headlight"))
        c = pl.camera
        c.position = tuple(o)
        c.focal_point = tuple(o + f)
        c.up = tuple(up)
        c.view_angle = float(np.degrees(2.0 * np.arctan(
            np.tan(np.radians(cam.fov) / 2.0) * cam.ny / cam.nx)))
        pl.reset_camera_clipping_range()
        img = np.asarray(pl.screenshot(return_img=True), float)[..., :3]
    finally:
        pl.close()
    return img / 255.0
