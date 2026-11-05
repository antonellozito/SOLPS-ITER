#!/usr/bin/env python3
"""plot_residuals.py [--no-show]

Python version of plot_residuals: the pages of resco, resmo, reshe and
reshi in residuals.ps and in a window with a tab each
(lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "plot_residuals"]
         + sys.argv[1:])
