#!/usr/bin/env python3
"""energy_balance_tracing.py [--rolling N | --batch N] [--no-show]

Python version of energy_balance_tracing: the energy balance from
tracing/blne.trc in energy_balance.ps and in a window with a tab per page
(lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "energy_balance_tracing"]
         + sys.argv[1:])
