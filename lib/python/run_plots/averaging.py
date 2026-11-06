"""Rolling and batch averages of time series (off unless asked for).

rolling N: each value becomes the mean of the values within N//2 slices
on either side, the window cut at the ends of the series.
batch N: consecutive blocks of N slices from the first one, each replaced
by its mean (time too); an incomplete last block is dropped.
"""

import sys

import numpy as np


def rolling(y, n):
    y = np.asarray(y, dtype=float)
    half = int(n) // 2
    if half <= 0 or y.size == 0:
        return y
    sums = np.concatenate(([0.0], np.cumsum(y)))
    i = np.arange(y.size)
    lo = np.maximum(i - half, 0)
    hi = np.minimum(i + half + 1, y.size)
    return (sums[hi] - sums[lo]) / (hi - lo)


def batch(x, y, n):
    """(x, y) with each block of n slices replaced by its mean."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    n = int(n)
    m = min(x.size, y.size) // n if n > 0 else 0
    if m == 0:
        return x[:0], y[:0]
    return (x[:m * n].reshape(m, n).mean(axis=1),
            y[:m * n].reshape(m, n).mean(axis=1))


class Averaging:
    """The averaging asked on the command line (--rolling or --batch)."""

    def __init__(self, rolling_n=None, batch_n=None, name="run plot"):
        self.rolling_n, self.batch_n, self.name = rolling_n, batch_n, name
        self._warned = set()

    def __bool__(self):
        return bool(self.rolling_n or self.batch_n)

    def describe(self):
        if self.rolling_n:
            return "rolling average over %d slices" % self.rolling_n
        if self.batch_n:
            return "batch average over %d slices" % self.batch_n
        return ""

    def apply(self, x, y):
        if self.rolling_n:
            return np.asarray(x, dtype=float), rolling(y, self.rolling_n)
        if self.batch_n:
            left = min(len(x), len(y)) % self.batch_n
            if left and left not in self._warned:
                self._warned.add(left)
                sys.stderr.write("%s: batch average: last %d time slice(s) "
                                 "dropped (incomplete block)\n"
                                 % (self.name, left))
            return batch(x, y, self.batch_n)
        return np.asarray(x, dtype=float), np.asarray(y, dtype=float)
