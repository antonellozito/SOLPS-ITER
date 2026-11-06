"""Multipage PostScript of matplotlib figures, one figure per page (the
b2plot pages and the run plots)."""

import io

import matplotlib


def _ps_page(fig, orientation="portrait"):
    buf = io.BytesIO()
    with matplotlib.rc_context({"ps.papersize": "letter"}):
        fig.savefig(buf, format="ps", orientation=orientation)
    return buf.getvalue().decode("latin-1")


def write_ps(figures, path, orientation="portrait", creator="SOLPS-ITER"):
    """Multi-page PostScript, each page a matplotlib page on US letter.

    The NCAR frame lands where NCAR puts it: matplotlib centres the
    7.5 inch square on the letter page, i.e. at (36,126)-(576,666) pt.
    The run plots use landscape pages, as gnuplot.
    """
    with open(path, "w", encoding="latin-1") as out:
        out.write(f"%!PS-Adobe-3.0\n%%Creator: {creator}\n"
                  f"%%Pages: {len(figures)}\n%%BoundingBox: 0 0 612 792\n"
                  + ("%%Orientation: Landscape\n"
                     if orientation == "landscape" else "")
                  + "%%DocumentPaperSizes: Letter\n%%EndComments\n")
        for i, fig in enumerate(figures, 1):
            body = [l for l in _ps_page(fig, orientation).splitlines()
                    if not l.startswith(("%%", "%!"))]
            out.write(f"%%Page: {i} {i}\n/solpspy_page save def\n")
            out.write("\n".join(body))
            out.write("\nclear solpspy_page restore\n")
        out.write("%%Trailer\n%%EOF\n")
