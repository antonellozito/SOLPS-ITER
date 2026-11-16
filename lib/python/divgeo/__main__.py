"""DivGeo with the Python interface, run as
python $SOLPSTOP/lib/python/divgeo [DivGeo options] [files]

The command line is that of the Motif DivGeo (dg.exe): the program name is
dg.exe, so the configuration dg.dgc and the help file dg.dgh are taken
from the current folder unless -cfg is given.

Any Python 3 syntax up to the requirements check, so that an old
interpreter still prints the requirements message.
"""

import os
import sys

if not __package__:
    # run as a directory or file: load lib/python as the package solpspy
    # (as lib/python/__main__.py does), with this directory in it
    import importlib.util
    _here = os.path.dirname(os.path.realpath(__file__))
    _top = os.path.dirname(_here)
    sys.path = [p for p in sys.path
                if os.path.realpath(p or ".") not in (_here, _top)]
    _spec = importlib.util.spec_from_file_location(
        "solpspy", os.path.join(_top, "__init__.py"),
        submodule_search_locations=[_top])
    sys.modules["solpspy"] = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(sys.modules["solpspy"])

from solpspy import requirements  # noqa: E402

PROGRAM = "dg.exe"


def main(argv=None):
    words = sys.argv[1:] if argv is None else list(argv)
    requirements.NAME = "dg"
    requirements.GRAPHICS_OF = "DivGeo"
    requirements.check(True)
    from solpspy.divgeo.app import application
    return application.main([PROGRAM] + words)


if __name__ == "__main__":
    sys.exit(main())
