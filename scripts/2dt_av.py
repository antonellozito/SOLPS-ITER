#!/usr/bin/env python3
"""2dt_av.py [-lx] [-ly] [--rolling N | --batch N] [--no-show] NAME...

Python version of 2dt_av: the averaged time traces of b2batch.nc (b2time.nc
without it) against time, in a window (lib/python/run_plots); -h for the
options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2dt_av"]
         + sys.argv[1:])
