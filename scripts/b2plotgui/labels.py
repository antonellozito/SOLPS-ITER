"""Translate NCAR Plotchar function codes into matplotlib mathtext.

b2plot labels use Plotchar function codes between two function-code
characters (FC, "@" after customise_label): S superscript, B subscript,
N normal level, G or F33 Greek, R, F0 or F25 Roman, F18 math symbols,
Zn size change (ignored).
"""

import re

GREEK = {
    "a": r"\alpha", "b": r"\beta", "c": r"\chi", "d": r"\delta",
    "e": r"\epsilon", "f": r"\phi", "g": r"\gamma", "h": r"\eta",
    "i": r"\iota", "j": r"\vartheta", "k": r"\kappa", "l": r"\lambda",
    "m": r"\mu", "n": r"\nu", "o": "o", "p": r"\pi", "q": r"\theta",
    "r": r"\rho", "s": r"\sigma", "t": r"\tau", "u": r"\upsilon",
    "v": r"\varsigma", "w": r"\omega", "x": r"\xi", "y": r"\psi",
    "z": r"\zeta",
    "A": "A", "B": "B", "C": "X", "D": r"\Delta", "E": "E", "F": r"\Phi",
    "G": r"\Gamma", "H": "H", "I": "I", "J": r"\Theta", "K": "K",
    "L": r"\Lambda", "M": "M", "N": "N", "O": "O", "P": r"\Pi",
    "Q": r"\Theta", "R": "P", "S": r"\Sigma", "T": "T", "U": r"\Upsilon",
    "V": r"\varsigma", "W": r"\Omega", "X": r"\Xi", "Y": r"\Psi",
    "Z": "Z",
}

_MATH_SPECIAL = re.compile(r"([\\{}^_%$#&~])")


def _math_text(s):
    """Upright text inside a math island."""
    s = _MATH_SPECIAL.sub(r"\\\1", s).replace(" ", r"\ ")
    return r"\mathrm{" + s + "}" if s else ""


def _math_greek(s):
    return "".join(GREEK.get(c, _math_text(c)) for c in s)


def _codes(s, fc):
    """Split s into (kind, value) tokens: ("text", str) or ("code", str)."""
    if not fc or fc not in s:
        return [("text", s)]
    tokens = []
    parts = s.split(fc)
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:
                tokens.append(("text", part))
        elif part:
            tokens.append(("code", part.upper()))
    if len(parts) % 2 == 0 and parts[-1]:
        # an unpaired function-code character: keep the rest as text
        tokens[-1] = ("text", fc + parts[-1])
    return tokens


def plain_text(s, fc="@"):
    """s without its Plotchar function codes (for window titles)."""
    return "".join(v for kind, v in _codes(s, fc) if kind == "text")


def to_mathtext(s, fc="@"):
    """Return s with its Plotchar function codes as matplotlib mathtext."""
    level = ""        # "", "^" or "_"
    greek = False
    out = []
    island = []       # math pieces of the current super/subscript run

    def flush():
        if island:
            out.append("$" + level + "{" + "".join(island) + "}$")
            island.clear()

    for kind, value in _codes(s, fc):
        if kind == "code":
            code = value.strip()
            if code in ("S", "B"):
                flush()
                level = "^" if code == "S" else "_"
            elif code == "N":
                flush()
                level = ""
            elif code in ("G", "F33"):
                greek = True
            elif code in ("R", "F0", "F25", "F1"):
                greek = False
            continue
        if level:
            island.append(_math_greek(value) if greek else _math_text(value))
        elif greek:
            out.append("$" + _math_greek(value) + "$")
        else:
            out.append(value.replace("$", r"\$"))
    flush()
    return "".join(out)
