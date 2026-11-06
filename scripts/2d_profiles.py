#!/usr/bin/env python3
"""2d_profiles.py [--rolling N | --batch N] [--no-show] [NUM [END]]

Python version of 2d_profiles: the profiles in 2d_profiles/*.last10 and
the pages in b2time2d_profiles.ps and in a window with a tab per page
(lib/python/run_plots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2d_profiles"]
         + sys.argv[1:])
