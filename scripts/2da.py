#!/usr/bin/env python3
"""2da.py [-s FILE] [--rolling N | --batch N] NAME...

Python version of 2da: a table of b2time.nc quantities on standard output,
as 2da writes it (lib/python/runplots); -h for the options.
"""

import os
import sys

ENTRY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir,
                     "lib", "python")
os.execv(sys.executable,
         [sys.executable, ENTRY, "--run-plot", "2da"]
         + sys.argv[1:])
