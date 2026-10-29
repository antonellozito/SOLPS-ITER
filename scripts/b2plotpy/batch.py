"""CLI parity mode: b2plot commands on stdin, NCAR-like pages out.

    echo "phys te surf" | b2plot.py [-s] [-o OUT]

The stdin lines go unchanged to b2pl_gui.exe, followed by "1 sync" and
"quit"; lines with wall commands are skipped (see WALL).
Each page opens in a matplotlib window (NCAR-like by default; zoom, pan
and save in any matplotlib format from its toolbar), and is written to
-o if given.
"""

import io
import os
import re
import sys

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages

from . import backend, labels, options, protocol, render, scene

# Wall quantities and wall functions of b2plot (wlabels, wfns of
# b2mod_b2plot_help.F): b2plot sets up the wall stack only under WG_TODO,
# so input lines that use them are skipped instead of stopping b2plot
WALL = frozenset("""
    wallarea ei wallflux wallhflx r1 r2 z1 z2 walltemp plathick cooltemp
    vaprtemp north south west east nseg iwlt iweq iwgt iswlt isweq iswgt
    ibnd walldist wallngth sput sput2 sputchem thermev sputres backscat
    backscae erosion deposit ero_ml depo_ml time imapx imapy kappa_a
    kappa_b kappa_a1 kappa_a2 kappa_a3 kappa_a4 kappapa1 kappapa2
    kappapa3 kappapa4 tgdns cp_b1 cp_b2 cp_b3 erel bbdyemis vapprs_a
    vapprs_b vapprs qevap qrad stckcoef sublheat ckappa_a ckappa_b
    ckappaa1 ckappaa2 ckappaa3 ckappaa4 ckapppa1 ckapppa2 ckapppa3
    ckapppa4 ctgdns c_cp_b1 c_cp_b2 c_cp_b3 coathick lkappa lrho lcp
    lemis sputfrac lthick ldepth iwle iwge iswle iswge c_cp_b4 cp_b4
    kappa_a5 kappapa5 ckappaa5 ckapppa5 iwne iswne
    wall wall_ank logw linw logxw linxw plwl sumw intw intw* pswa wclvs
    wclvd wclvn wclvp wwid wabs ddw wsumz pwne wm+ wm- wm* wm/ rwm+ rwm-
    rwm* rwm/ rwm** wdrop wdup wswap wover wsel wzsel wmmin wmmax rwmmi
    rwmma wmlt wmle wmeq wmne wmgt wmge wlog wln wsqrt wexp wzrng wchs
    wtos wtot wpos wsaw wallf outpw wprt wtab wlld woff wlist
""".split())
_TOKEN = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"|(\S+)")


def _ps_page(fig):
    buf = io.BytesIO()
    with matplotlib.rc_context({"ps.papersize": "letter"}):
        fig.savefig(buf, format="ps", orientation="portrait")
    return buf.getvalue().decode("latin-1")


def write_ps(figures, path):
    """Multi-page PostScript, each page a matplotlib page on US letter.

    The NCAR frame lands where NCAR puts it: matplotlib centres the
    7.5 inch square on the letter page, i.e. at (36,126)-(576,666) pt.
    """
    with open(path, "w", encoding="latin-1") as out:
        out.write("%!PS-Adobe-3.0\n%%Creator: b2plot.py\n"
                  f"%%Pages: {len(figures)}\n%%BoundingBox: 0 0 612 792\n"
                  "%%DocumentPaperSizes: Letter\n%%EndComments\n")
        for i, fig in enumerate(figures, 1):
            body = [l for l in _ps_page(fig).splitlines()
                    if not l.startswith(("%%", "%!"))]
            out.write(f"%%Page: {i} {i}\n/b2plotpy_page save def\n")
            out.write("\n".join(body))
            out.write("\nclear b2plotpy_page restore\n")
        out.write("%%Trailer\n%%EOF\n")


def write_output(figures, path, dpi):
    """-o: one multipage PDF, or numbered PNG/SVG/EPS files."""
    root, ext = os.path.splitext(path)
    if ext.lower() == ".pdf":
        with PdfPages(path) as pdf:
            for fig in figures:
                pdf.savefig(fig)
        return [path]
    if ext.lower() == ".ps":
        write_ps(figures, path)
        return [path]
    names = []
    for i, fig in enumerate(figures, 1):
        name = f"{root}_{i:03d}{ext}"
        fig.savefig(name, dpi=dpi)
        names.append(name)
    return names


def wall_commands(line):
    """Wall commands of a b2plot input line, outside quoted strings and
    comments (lines starting with *, ! or #; ! starts a comment)."""
    if line[:1] in ("*", "!", "#"):
        return []
    out = []
    for m in _TOKEN.finditer(line):
        word = m.group(1)
        if word is None:
            continue
        if word.startswith("!"):
            break
        word = word.split("!", 1)[0]
        if word in WALL:
            out.append(word)
    return out


def without_wall(lines):
    """The input lines without wall commands, telling which are skipped."""
    kept = []
    for line in lines:
        if wall_commands(line):
            print("b2plot.py: wall data are not available in this version "
                  "of b2plot, line skipped: %s" % line.strip(),
                  file=sys.stderr)
        else:
            kept.append(line)
    return kept


def run_commands(cmd, rundir, lines, record=None, console=sys.stdout):
    """Run b2pl_gui.exe on the command lines; return the Scene and status."""
    sc = scene.Scene()
    be = backend.Backend(cmd, rundir, record)
    be.start()
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
            print(f"b2plot.py: protocol error: {event[1]}", file=sys.stderr)
        elif event[0] == "exit":
            status = event[1]
    be.stop()
    return sc, status, bye


def show(frames):
    """One matplotlib window per page (QtAgg on PySide6); wait until closed."""
    os.environ.setdefault("QT_API", "pyside6")
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    figures = []
    for i, frame in enumerate(frames, 1):
        title = next((m["title"] for m in frame.meta if m["title"]), "")
        name = f"b2plot.py page {i}" + (f": {labels.plain_text(title)}"
                                        if title else "")
        fig = plt.figure(num=name, clear=True)
        figures.append(render.render_frame(frame, fig=fig))
    plt.show()
    return figures


def replay(path):
    sc = scene.Scene()
    with open(path, "rb") as stream:
        for op, payload in protocol.read_messages(stream):
            sc.feed(op, payload)
    return sc


def main(args):
    """CLI parity mode for the parsed b2plot.py options (options.py)."""
    if args.replay:
        sc, status, bye = replay(args.replay), 0, True
    else:
        lines = without_wall(sys.stdin.read().splitlines())
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
    if args.output and frames:
        figures = []
        for frame in frames:
            fig = render.render_frame(frame)
            FigureCanvasAgg(fig)
            figures.append(fig)
        for name in write_output(figures, args.output, args.dpi):
            print(f"b2plot.py: written {name}", file=sys.stderr)
    if frames and not args.no_show:
        show(frames)
    if not bye:
        print(f"b2plot.py: b2pl_gui.exe ended without BYE (exit status "
              f"{status})", file=sys.stderr)
        return 1
    return 0 if status == 0 else 1


if __name__ == "__main__":
    sys.exit(main(options.parse()))
