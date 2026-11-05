#!/usr/bin/env python3
"""2dds.py [-lx] [-ly] [--rolling N | --batch N] [--no-show] NAME...
          [NUM [END]]

Python version of 2dds: b2time.nc profiles against their ds coordinate,
means over the last NUM time slices up to END, in a window
(lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2dds"]
         + sys.argv[1:])
