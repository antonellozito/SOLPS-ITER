#!/usr/bin/env python3
"""2d_plots_av.py [--rolling N | --batch N] [--no-show]

Python version of 2d_plots_av: the averaged time traces of b2batch.nc in
b2time2d_time_traces_av.ps and in a window with a tab per page
(lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2d_plots_av"]
         + sys.argv[1:])
