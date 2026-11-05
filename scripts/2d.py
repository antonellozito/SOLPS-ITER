#!/usr/bin/env python3
"""2d.py [-lx] [-ly] [--rolling N | --batch N] [--no-show] X NAME...

Python version of 2d: b2time.nc quantities against the quantity X, in a
window (lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2d"]
         + sys.argv[1:])
