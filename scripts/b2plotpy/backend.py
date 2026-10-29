"""Run b2pl_py.exe as a child process with a FIFO for its messages.

Python never calls Fortran routines: b2plot command text goes to the
child's stdin, binary messages come back on the FIFO named by
B2PLOT_GUI_FIFO, console text on stdout.
"""

import os
import queue
import shutil
import signal
import subprocess
import tempfile
import threading

from . import protocol


def wrapper_command(standalone=False, targets=("b2pl_py",), debugger=None,
                    dry_run=False):
    """The scripts/b2plot command that stages and runs the executable."""
    cmd = [os.path.join(os.environ["SOLPSTOP"], "scripts", "b2plot")]
    cmd += ["-n"] if dry_run else []
    cmd += ["-s"] if standalone else []
    cmd += ["-d", debugger] if debugger else []
    return cmd + list(targets)


def command(args):
    """Child command for the b2plot.py options (--exe or the wrapper)."""
    if args.exe:
        return [os.path.abspath(args.exe)]
    return wrapper_command(args.standalone, args.targets, args.debugger)


class Backend:
    """One b2plot child process and its message and console streams."""

    def __init__(self, cmd, rundir=".", record=None):
        self.cmd = cmd
        self.rundir = rundir
        self.record = record
        self.events = queue.Queue()
        self.proc = None
        self.tmp = None
        self.fifo = None
        self._opened = threading.Event()
        self._threads = []

    def start(self):
        self.tmp = tempfile.mkdtemp(prefix="b2plotpy-")
        self.fifo = os.path.join(self.tmp, "gui.fifo")
        os.mkfifo(self.fifo, 0o600)
        # the FIFO reader must wait for the writer before the child starts
        self._thread(self._read_fifo)
        env = dict(os.environ, B2PLOT_GUI_FIFO=self.fifo,
                   GFORTRAN_UNBUFFERED_PRECONNECTED="y")
        self.proc = subprocess.Popen(
            self.cmd, cwd=self.rundir, env=env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            bufsize=1, start_new_session=True)
        self._thread(self._read_stdout)
        self._thread(self._watch_exit)

    def _thread(self, target):
        t = threading.Thread(target=target, daemon=True)
        t.start()
        self._threads.append(t)

    def _read_fifo(self):
        try:
            with open(self.fifo, "rb", buffering=0) as stream:
                self._opened.set()
                for op, payload in protocol.read_messages(stream, self.record):
                    self.events.put(("message", op, payload))
        except protocol.ProtocolError as err:
            self.events.put(("error", str(err)))
        self.events.put(("eof",))

    def _read_stdout(self):
        for line in self.proc.stdout:
            self.events.put(("console", line))
        self.events.put(("console_eof",))

    def _watch_exit(self):
        status = self.proc.wait()
        if not self._opened.is_set():
            # the child ended before opening the FIFO: release the reader
            try:
                os.close(os.open(self.fifo, os.O_WRONLY | os.O_NONBLOCK))
            except OSError:
                self.events.put(("eof",))
        self.events.put(("exit", status))

    def send(self, text):
        """Write command text to the child; False if it has stopped."""
        try:
            self.proc.stdin.write(text)
            self.proc.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            return False

    def close_input(self):
        try:
            self.proc.stdin.close()
        except (BrokenPipeError, ValueError):
            pass

    def iter_events(self):
        """Yield events until the FIFO, stdout and the process have ended."""
        pending = {"eof", "console_eof", "exit"}
        while pending:
            event = self.events.get()
            pending.discard(event[0])
            yield event

    def stop(self, timeout=5.0):
        """End the child (quit, then SIGTERM and SIGKILL) and clean up."""
        if self.proc is not None and self.proc.poll() is None:
            self.send("quit\n")
            try:
                self.proc.wait(timeout)
            except subprocess.TimeoutExpired:
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(self.proc.pid, sig)
                        self.proc.wait(2.0)
                        break
                    except (ProcessLookupError, subprocess.TimeoutExpired):
                        continue
        if self.proc is not None and self.proc.poll() is not None:
            for t in self._threads:
                t.join(2.0)
            for stream in (self.proc.stdin, self.proc.stdout):
                try:
                    stream.close()
                except (BrokenPipeError, ValueError):
                    pass
        if self.tmp is not None:
            shutil.rmtree(self.tmp, ignore_errors=True)
            self.tmp = None
