#!/usr/bin/env python3
"""check_python.py

Exit status 0 when the Python of this SOLPS-ITER session (the local
installation of install_python, else $PYTHON, else this python3) can run
the Python versions of the plot scripts without windows, else 1 with the
missing modules (lib/python/runplots); used by summarize_run.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "check_python"]
         + sys.argv[1:])
