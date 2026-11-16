"""The two kinds of balance of a volume, each with the same two parts:
the balance of each unit between its two ends (the "ends" part: the flux
in and out of it) and the balance across the boundaries between the
units (the "cut" part). The parallel balance follows the field lines:
its units with ends are the flux tubes (from the upstream to the
downstream surface), the slices are cut. The radial balance goes across
the flux surfaces: its units with ends are the slices (from the inner to
the outer flux surface), the flux tubes are cut."""

from dataclasses import dataclass

from .terms import POLOIDAL, RADIAL


@dataclass(frozen=True)
class Kind:
    key: str
    name: str                       # title, status messages
    button: str                     # text of its button
    tip: str                        # tooltip of its button
    ends_units: str                 # "tubes" or "slices"
    transport: str                  # the sources of the transport into a
    group: str                      # unit through its other faces
    flux_role: str                  # the flux balanced: "flux" (poloidal
    #                                 component) or "radial" (equations)
    from_end: bool                  # slice distances from the end (else
    #                                 from the start) of the tube
    hz_without_area: bool           # no area: the mean hz factor at the
    #                                 end (else 1)
    area_types: tuple
    area_ends: tuple                # the first one: the outflow end
    area_tip: str                   # tooltip of the choice of the end
    left_out: tuple = ()            # quantities defined in the other only
    left_out_why: str = ""

    def axis(self, part):
        """"radial" (radial coordinate of the tubes) or "poloidal"
        (distance along the tubes) of part "ends" or "cut"."""
        tubes = (part == "ends") == (self.ends_units == "tubes")
        return "radial" if tubes else "poloidal"

    def part(self, axis):
        """The part whose points are along axis."""
        return "ends" if self.axis("ends") == axis else "cut"


PARALLEL = Kind(
    "parallel", "Parallel balance", "Parallel fluxes",
    "Pick the upstream and the downstream surface of a volume on the plot "
    "(both in one region: core, SOL or PFR); the balances of balance.nc "
    "along the field lines in it appear below",
    "tubes", "Radial transport", RADIAL, "flux", True, True,
    (("none", "None"), ("parallel", "Parallel"), ("contact", "Contact")),
    (("down", "Downstream"), ("up", "Upstream")),
    "End of each flux tube whose area divides its fluxes and sources")
RADIAL_KIND = Kind(
    "radial", "Radial balance", "Radial fluxes",
    "Pick the inner and the outer flux surface of a volume on the plot "
    "(both in one region: core, SOL or PFR); the balances of balance.nc "
    "across the flux surfaces in it appear below",
    "slices", "Poloidal transport", POLOIDAL, "radial", False, False,
    (("none", "None"), ("contact", "Contact")),
    (("outer", "Outer"), ("inner", "Inner")),
    "Surface whose contact area divides the fluxes and sources",
    ("force", "totpress"), "Defined along the field lines only")
KINDS = {k.key: k for k in (PARALLEL, RADIAL_KIND)}
