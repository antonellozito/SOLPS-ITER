#!/usr/bin/env python3
"""resco.py [-m MOD] [-l LAST] [-a AVE] [--no-show]

Python version of resco: norms of the continuity residuals of b2ftrace per
species against the iteration, in a window (lib/python/runplots); -h for
the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "resco"]
         + sys.argv[1:])
