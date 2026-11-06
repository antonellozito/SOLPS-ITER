#!/usr/bin/env python3
"""2d_profiles_extended.py [--rolling N | --batch N] [NUM]

Python version of 2d_profiles_extended: more profiles in *.last10 of the
run folder (lib/python/run_plots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2d_profiles_extended"]
         + sys.argv[1:])
