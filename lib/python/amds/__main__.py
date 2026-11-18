"""AMDS with the Python interface, run as
python $SOLPSTOP/lib/python/amds [AMDS options] [files]

The command line is that of the Motif program: its name (argv[0], from
which the database, the configuration and the data folder are found when
the AMDS variables and resources do not give them) is the path the Motif
amds has in the build folder.
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


def program():
    """argv[0] of the Motif amds as scripts/amds starts it."""
    env = os.environ
    return os.path.join(env.get("SOLPSTOP", ""), "modules", "amds", "builds",
                        "%s.%s" % (env.get("HOST_NAME", ""),
                                   env.get("COMPILER", "")), "amds")


def main(argv=None):
    words = sys.argv[1:] if argv is None else list(argv)
    requirements.NAME = "amds"
    requirements.GRAPHICS_OF = "AMDS"
    requirements.MANUAL = "section \"modules/amds\""
    requirements.check(True)
    from solpspy.amds.app import application
    return application.main([program()] + words)


if __name__ == "__main__":
    sys.exit(main())
