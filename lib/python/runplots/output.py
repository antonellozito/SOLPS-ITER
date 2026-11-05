"""Output of the run plots: the PostScript file of the old script, the
PRINT_PLOT file of the one-page tools, and the window with a tab per page.

PySide6 is needed only when the window opens: on a display, without
--no-show and, for a one-page tool, without PRINT_PLOT (as the old plot
script, which then writes PostScript instead of opening a window).
"""

import os
import sys

from .. import options, requirements


def output_path(name):
    """Output files go to GNUPLOT_TMP when it is set, as with gnuplot."""
    folder = os.environ.get("GNUPLOT_TMP")
    return os.path.join(folder, name) if folder else name


class Output:
    def __init__(self, name, args, one_page=False, extra=()):
        self.name, self.one_page = name, one_page
        self.print_plot = os.environ.get("PRINT_PLOT") if one_page else None
        self.wanted = not args.no_show and not self.print_plot
        self.show = self.wanted and options.display_available()
        found = requirements.problems(self.show, extra)
        if found:
            requirements.fail(found, extra)

    def deliver(self, title, pages, ps=None):
        """Draw the pages, write the file, open the window."""
        if not pages:
            sys.stderr.write("%s.py: nothing to draw\n" % self.name)
            return 1
        from .. import batch
        from . import pages as page_module
        figures = [page_module.draw(p) for p in pages]
        target = self.print_plot or ps
        if target:
            batch.write_ps(figures, output_path(target),
                           orientation="landscape", creator=self.name)
        if self.show:
            from . import window
            window.show("%s.py: %s" % (self.name, title), pages, figures)
        elif self.wanted:
            sys.stderr.write("%s.py: no display, window skipped\n"
                             % self.name)
        return 0
