"""Debug tool: run b2pl_py.exe (or replay a recording) and print its messages.

    python3 -m b2plotpy.dump [options] [COMMANDS]

COMMANDS is a file of b2plot commands, one batch per line (default: stdin).
Each batch is followed by "<n> sync"; "quit" is sent at the end.
"""

import argparse
import collections
import os
import sys

import numpy as np

from . import backend, protocol


def _short(value):
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return f"{value.dtype}[0]"
        return (f"{value.dtype}[{value.size}] "
                f"{value.min():.6g}..{value.max():.6g}")
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, str):
        return repr(value if len(value) <= 60 else value[:57] + "...")
    if isinstance(value, list):
        if value and isinstance(value[0], tuple):
            return f"[{len(value)} categories]"
        return "[" + ", ".join(_short(v) for v in value[:8]) + \
            (", ..." if len(value) > 8 else "") + "]"
    return str(value)


def format_message(msg):
    """One line describing a decoded message."""
    if msg.name == "CATALOG":
        parts = [f"{name}={len(entries)}" for name, entries
                 in msg.categories]
        text = " ".join(parts)
    else:
        text = " ".join(f"{k}={_short(v)}" for k, v in msg.fields.items())
    if msg.extra:
        text += f" (+{msg.extra} unread bytes)"
    return f"{msg.op:3d} {msg.name:<13s} {text}"


class Dumper:
    """Decode and print messages, keeping per-opcode counts."""

    def __init__(self, quiet=False):
        self.quiet = quiet
        self.counts = collections.Counter()
        self.unknown = set()
        self.bye = False

    def feed(self, op, payload):
        msg = protocol.decode(op, payload)
        self.counts[msg.name] += 1
        if msg.name == "UNKNOWN" and op not in self.unknown:
            self.unknown.add(op)
            print(f"unknown opcode {op} skipped", file=sys.stderr)
        if msg.name == "BYE":
            self.bye = True
        if not self.quiet:
            print(format_message(msg), flush=True)

    def summary(self):
        print("message counts: " + ", ".join(
            f"{name} {n}" for name, n in sorted(self.counts.items())))


def replay(path, dumper):
    with open(path, "rb") as stream:
        for op, payload in protocol.read_messages(stream):
            dumper.feed(op, payload)


def run(cmd, rundir, batches, dumper, record=None, console=None):
    """Run cmd in rundir, send the batches, print the messages."""
    be = backend.Backend(cmd, rundir, record)
    be.start()
    text = "".join(f"{line}\n{i} sync\n" for i, line in enumerate(batches, 1))
    if not be.send(text + "quit\n"):
        print("b2plot ended before reading all commands", file=sys.stderr)
    be.close_input()
    status = None
    for event in be.iter_events():
        if event[0] == "message":
            dumper.feed(event[1], event[2])
        elif event[0] == "console" and console is not None:
            console.write(event[1])
            console.flush()
        elif event[0] == "error":
            print(f"protocol error: {event[1]}", file=sys.stderr)
        elif event[0] == "exit":
            status = event[1]
    be.stop()
    return status


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m b2plotpy.dump",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("commands", nargs="?",
                    help="file of command batches (default: stdin)")
    ap.add_argument("--exe", help="run this executable in --rundir instead "
                    "of the scripts/b2plot wrapper")
    ap.add_argument("--rundir", default=".", help="directory to run in")
    ap.add_argument("-s", action="store_true", dest="standalone",
                    help="standalone build (wrapper only)")
    ap.add_argument("--replay", help="decode a recorded stream")
    ap.add_argument("--record", help="also save the raw stream to a file")
    ap.add_argument("--console", help="write the b2plot console text to a "
                    "file (default: stderr)")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="print only the message counts")
    args = ap.parse_args(argv)

    dumper = Dumper(quiet=args.quiet)
    if args.replay:
        replay(args.replay, dumper)
        dumper.summary()
        return 0

    if args.commands:
        with open(args.commands) as f:
            lines = f.read().splitlines()
    else:
        lines = sys.stdin.read().splitlines()
    batches = [l for l in lines if l.strip() and not l.lstrip().startswith("#")]
    if args.exe:
        cmd = [os.path.abspath(args.exe)]
    else:
        cmd = backend.wrapper_command(args.standalone)
    record = open(args.record, "wb") if args.record else None
    console = open(args.console, "w") if args.console else sys.stderr
    try:
        status = run(cmd, args.rundir, batches, dumper, record, console)
    finally:
        if record is not None:
            record.close()
        if console is not sys.stderr:
            console.close()
    dumper.summary()
    print(f"exit status {status}, BYE {'received' if dumper.bye else 'missing'}")
    return 0 if (status == 0 and dumper.bye) else 1


if __name__ == "__main__":
    sys.exit(main())
