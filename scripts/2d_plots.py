#!/usr/bin/env python3
"""2d_plots.py [--rolling N | --batch N] [--no-show]

Python version of 2d_plots: the b2time.nc time traces in
b2time2d_time_traces.ps and in a window with a tab per page
(lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2d_plots"]
         + sys.argv[1:])
