#!/usr/bin/env python3
"""reshe.py [-m MOD] [-l LAST] [-a AVE] [--no-show]

Python version of reshe: norm of the residual of the electron energy
equation of b2ftrace against the iteration, in a window
(lib/python/run_plots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "reshe"]
         + sys.argv[1:])
