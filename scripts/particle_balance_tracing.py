#!/usr/bin/env python3
"""particle_balance_tracing.py [--rolling N | --batch N] [--no-show]

Python version of particle_balance_tracing: the particle balance of each
element from tracing/blnn_SPb.trc in particle_balance.ps and in a window
with a tab per page (lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "particle_balance_tracing"]
         + sys.argv[1:])
