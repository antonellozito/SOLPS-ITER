#!/usr/bin/env python3
"""2dt_tracing.py [-lx] [-ly] [--rolling N | --batch N] [--no-show] NAME...

Python version of 2dt_tracing: columns of tracing/blnn_SPb.trc and
tracing/blne.trc against time, in a window (lib/python/run_plots); -h for
the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2dt_tracing"]
         + sys.argv[1:])
