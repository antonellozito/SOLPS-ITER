"""Command line of the Python graphics: b2plot commands on stdin,
NCAR-like pages out.

    echo "phys te surf" | b2plot         (commands piped or redirected)
    b2plot                               (commands typed at the terminal)
    b2run b2yq                           (a B2 post-processor)

The stdin lines go unchanged to b2pl.exe, followed by "1 sync" and
"quit"; at a terminal each line goes at once, followed by a numbered sync.
B2PLOT_DEV chooses the output as in b2plot: with x11 each page opens in a
matplotlib window (NCAR-like; zoom, pan and save in any matplotlib format
from its toolbar), with ps the pages go to b2plot.ps in the run
directory; -o writes one more file. A post-processor writes PROGRAM.pdf.
"""

import os
import queue
import sys
import threading

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from . import backend, labels, options, protocol, render, scene
from .. import requirements
from ..postscript import write_ps


def write_output(figures, path, dpi):
    """-o: one multipage PDF, or numbered PNG/SVG/EPS files."""
    root, ext = os.path.splitext(path)
    if ext.lower() == ".pdf":
        with PdfPages(path) as pdf:
            for fig in figures:
                pdf.savefig(fig)
        return [path]
    if ext.lower() == ".ps":
        write_ps(figures, path, creator="b2plot")
        return [path]
    names = []
    for i, fig in enumerate(figures, 1):
        name = f"{root}_{i:03d}{ext}"
        fig.savefig(name, dpi=dpi)
        names.append(name)
    return names


def run_commands(cmd, rundir, lines, record=None, console=sys.stdout,
                 commands=True):
    """Run b2pl.exe on the command lines (or a B2 post-processor, which
    reads none); return the Scene and status."""
    sc = scene.Scene()
    be = backend.Backend(cmd, rundir, record)
    be.start()
    if commands:
        be.send("".join(line + "\n" for line in lines) + "1 sync\nquit\n")
    be.close_input()
    status, bye = None, False
    for event in be.iter_events():
        if event[0] == "message":
            sc.feed(event[1], event[2])
            bye = bye or event[1] == protocol.OPCODES["BYE"]
        elif event[0] == "console":
            console.write(event[1])
        elif event[0] == "error":
            print(f"b2plot: protocol error: {event[1]}", file=sys.stderr)
        elif event[0] == "exit":
            status = event[1]
    be.stop()
    return sc, status, bye


def _draw(frame, number, fig=None):
    """One page; a page that cannot be drawn is reported and kept as far
    as it got, so that the other pages are still shown and written."""
    fig = Figure() if fig is None else fig
    try:
        return render.render_frame(frame, fig=fig)
    except Exception as err:
        print(f"b2plot: page {number} could not be drawn: {err}",
              file=sys.stderr)
        return fig


def _pyplot():
    """pyplot on QtAgg (PySide6) for the page windows."""
    os.environ["QT_API"] = "pyside6"
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    return plt


def _window_name(frame, number):
    title = next((m["title"] for m in frame.meta if m["title"]), "")
    return f"b2plot page {number}" + (f": {labels.plain_text(title)}"
                                      if title else "")


def show(frames):
    """One matplotlib window per page (QtAgg on PySide6); wait until closed."""
    plt = _pyplot()
    figures = []
    for i, frame in enumerate(frames, 1):
        fig = plt.figure(num=_window_name(frame, i), clear=True)
        figures.append(_draw(frame, i, fig))
    plt.show()
    return figures


def write_frames(frames, path, dpi, stream=None, prefix="b2plot"):
    """Draw the frames off screen and write them to path (write_output)."""
    sys.stdout.flush()
    figures = []
    for i, frame in enumerate(frames, 1):
        fig = _draw(frame, i)
        FigureCanvasAgg(fig)
        figures.append(fig)
    for name in write_output(figures, path, dpi):
        print(f"{prefix}: written {name}", file=stream or sys.stderr)


def write_files(frames, args):
    """The files of B2PLOT_DEV (b2plot.ps with ps) and of -o."""
    dev = options.devices()
    if dev["cgm"]:
        print("b2plot: B2PLOT_DEV cgm: NCAR metafiles (gmeta) need the "
              "NCAR Graphics build (USE_NCAR), none written",
              file=sys.stderr)
    if frames and dev["ps"] and not args.replay:
        write_frames(frames, os.path.join(args.rundir, "b2plot.ps"),
                     args.dpi)
    if frames and args.output:
        write_frames(frames, args.output, args.dpi)
    if (dev["x11"] and not args.no_show
            and not requirements.display_available()):
        print("b2plot: no display, page windows skipped", file=sys.stderr)


def deliver(frames, args):
    """The pages as B2PLOT_DEV asks (b2plot.ps with ps, windows with x11),
    plus -o."""
    write_files(frames, args)
    if frames and options.windows(args):
        show(frames)


def replay(path):
    sc = scene.Scene()
    with open(path, "rb") as stream:
        for op, payload in protocol.read_messages(stream):
            sc.feed(op, payload)
    return sc


def main(args):
    """Commands from stdin, for the parsed options (options.py)."""
    if args.replay:
        sc, status, bye = replay(args.replay), 0, True
    else:
        lines = sys.stdin.read().splitlines()
        cmd = backend.command(args)
        record = open(args.record, "wb") if args.record else None
        try:
            sc, status, bye = run_commands(cmd, args.rundir, lines, record)
        finally:
            if record is not None:
                record.close()
    frames = list(sc.frames)
    if not sc.current.is_empty():
        frames.append(sc.current)
    deliver(frames, args)
    if not bye:
        print(f"b2plot: b2pl.exe ended without BYE (exit status "
              f"{status})", file=sys.stderr)
        return 1
    return 0 if status == 0 else 1


def run_program(args):
    """A B2 post-processor: its pages go to PROGRAM.pdf in the run
    directory, or to -o; no windows."""
    prog = options.program(args)
    cmd = backend.command(args)
    record = open(args.record, "wb") if args.record else None
    try:
        sc, status, bye = run_commands(cmd, args.rundir, [], record,
                                       commands=False)
    finally:
        if record is not None:
            record.close()
    frames = list(sc.frames)
    if not sc.current.is_empty():
        frames.append(sc.current)
    if frames:
        write_frames(frames, args.output or os.path.join(
            args.rundir, prog + ".pdf"), args.dpi)
    if not bye:
        print(f"b2plot: {prog}.exe ended without BYE (exit "
              f"status {status})", file=sys.stderr)
        return 1
    return 0 if status == 0 else 1


def run_carre(args):
    """carre.exe of Carre2, with the terminal and the output streams of the
    caller (it asks for missing input at the terminal): its pages go to
    carre.pdf in the run directory, or to -o; messages on stdout, since
    the carre2 script sends stderr to carre.log."""
    path = args.output or os.path.join(args.rundir, "carre.pdf")
    if os.path.exists(path):
        os.remove(path)
    sc = scene.Scene()
    record = open(args.record, "wb") if args.record else None
    be = backend.Backend(backend.command(args), args.rundir, record,
                         terminal=True)
    status = None
    try:
        be.start()
        for event in be.iter_events():
            if event[0] == "message":
                sc.feed(event[1], event[2])
            elif event[0] == "error":
                print(f"carre2: protocol error: {event[1]}")
            elif event[0] == "exit":
                status = event[1]
    except KeyboardInterrupt:
        status = be.proc.wait() if be.proc is not None else 1
    finally:
        be.stop()
        if record is not None:
            record.close()
    frames = list(sc.frames)
    if not sc.current.is_empty():
        frames.append(sc.current)
    if frames:
        write_frames(frames, path, args.dpi, sys.stdout, "carre2")
    return status if status is not None and status >= 0 else 1


def _terminal(lines):
    """Lines typed at the terminal, None at the end of input."""
    try:
        import readline  # noqa: F401  (line editing and history)
    except ImportError:
        pass
    while True:
        try:
            lines.put(input())
        except (EOFError, KeyboardInterrupt):
            lines.put(None)
            return


class _Windows:
    """Page windows kept up to date while b2plot draws (interactive CLI)."""

    def __init__(self):
        self.plt = _pyplot()
        self.plt.ion()
        self.figures = []
        self.current = None

    def update(self, sc):
        for i in range(len(self.figures), len(sc.frames)):
            fig = self.current or self.plt.figure(
                num=_window_name(sc.frames[i], i + 1))
            self.current = None
            self.figures.append(_draw(sc.frames[i], i + 1, fig))
            fig.canvas.draw_idle()
        if not sc.current.is_empty():
            n = len(self.figures) + 1
            if self.current is None:
                self.current = self.plt.figure(
                    num=_window_name(sc.current, n))
            _draw(sc.current, n, self.current)
            self.current.canvas.draw_idle()
        self.plt.show(block=False)

    def pause(self):
        self.plt.pause(0.02)

    def wait(self):
        """Keep the windows until they are closed."""
        if self.plt.get_fignums():
            print("b2plot: close the page windows to end",
                  file=sys.stderr)
            self.plt.ioff()
            self.plt.show()


def interactive(args):
    """b2plot at a terminal: each typed line goes to b2pl.exe at once,
    followed by a numbered sync; with B2PLOT_DEV x11 the pages open in
    windows as b2plot draws them and stay open after quit until closed;
    with ps they go to b2plot.ps at the end."""
    record = open(args.record, "wb") if args.record else None
    sc = scene.Scene()
    be = backend.Backend(backend.command(args), args.rundir, record)
    be.start()
    lines = queue.Queue()
    threading.Thread(target=_terminal, args=(lines,), daemon=True).start()
    win = _Windows() if options.windows(args) else None
    pending = {"eof", "console_eof", "exit"}
    status, bye, nsync, reading, dirty = None, False, 0, True, False
    try:
        while pending:
            while reading:
                try:
                    line = lines.get_nowait()
                except queue.Empty:
                    break
                if line is None:
                    be.send("quit\n")
                    be.close_input()
                    reading = False
                else:
                    nsync += 1
                    be.send(f"{line}\n{nsync} sync\n")
            try:
                event = be.events.get(timeout=0.05)
            except queue.Empty:
                event = None
            while event is not None:
                pending.discard(event[0])
                if event[0] == "message":
                    sc.feed(event[1], event[2])
                    bye = bye or event[1] == protocol.OPCODES["BYE"]
                    dirty = dirty or event[1] in (
                        protocol.OPCODES["SYNC"], protocol.OPCODES["FRAME"])
                elif event[0] == "console":
                    sys.stdout.write(event[1])
                    sys.stdout.flush()
                elif event[0] == "error":
                    print(f"b2plot: protocol error: {event[1]}",
                          file=sys.stderr)
                elif event[0] == "exit":
                    status = event[1]
                try:
                    event = be.events.get_nowait()
                except queue.Empty:
                    event = None
            if win is not None:
                if dirty:
                    win.update(sc)
                    dirty = False
                win.pause()
    except KeyboardInterrupt:
        print("", file=sys.stderr)
    finally:
        be.stop()
        if record is not None:
            record.close()
    frames = list(sc.frames)
    if not sc.current.is_empty():
        frames.append(sc.current)
    if win is not None:
        win.update(sc)
    write_files(frames, args)
    if win is not None:
        win.wait()
    if not bye:
        print(f"b2plot: b2pl.exe ended without BYE (exit status "
              f"{status})", file=sys.stderr)
        return 1
    return 0 if status == 0 else 1
