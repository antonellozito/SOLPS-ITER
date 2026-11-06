#!/usr/bin/env python3
"""2dt.py [-lx] [-ly] [--rolling N | --batch N] [--no-show] NAME...

Python version of 2dt: b2time.nc time traces against time, in a window
(lib/python/run_plots); species as nasepm1 or dabsepm0, also several names
in one argument ("nesepa nesepm"); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2dt"]
         + sys.argv[1:])
