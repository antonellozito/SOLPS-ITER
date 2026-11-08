"""Derived quantities: expressions in the usual notation, translated to the
b2plot stack operations that compute them (b2plot does the arithmetic).

    ti/te    sqrt(ddx(te)**2 + ddy(te)**2)    te > 10    pvol(sna)
    sel(na, 1)*ne    sumz(na, 2, 9)    etos(pdena)    ixeq(10)
    samju('AMJUEL', 'H.4', '2.1.5', 'EI', te, ne)    adas('scd')

Quantity names come out as {name}, so that movie frames can stand for
them (data.Run); numbers become b2plot reals, constants (pi, qe, ...)
the b2plot constants.
"""

import ast
import re

FIELD_OPS = {ast.Add: "m+", ast.Sub: "m-", ast.Mult: "m*", ast.Div: "m/"}
REAL_OPS = {ast.Add: "rm+", ast.Sub: "rm-", ast.Mult: "rm*", ast.Div: "rm/",
            ast.Pow: "rm**"}
COMPARE = {ast.Lt: "mlt", ast.LtE: "mle", ast.Eq: "meq", ast.NotEq: "mne",
           ast.Gt: "mgt", ast.GtE: "mge"}
MIRROR = {ast.Lt: ast.Gt, ast.LtE: ast.GtE, ast.Gt: ast.Lt, ast.GtE: ast.LtE,
          ast.Eq: ast.Eq, ast.NotEq: ast.NotEq}
UNARY = ("abs", "log", "ln", "sqrt", "exp", "pos")      # e prefix on Eirene
MATRIX_ONLY = ("pvol", "pne", "psx", "psy", "psxperp", "ddx", "ddy", "sumft",
               "intx", "bala")
EIRENE_ONLY = ("psta", "pstv")
FITS = {"amju": ("matrix", 0), "samju": ("matrix", 2),
        "eamju": ("eirene", 2)}        # 4 strings, then up to n fields
INTEGERS = {"nspe": 3, "npec": 4}      # integer arguments, matrix result
FUNCTIONS = (UNARY + MATRIX_ONLY + EIRENE_ONLY + tuple(FITS)
             + tuple(INTEGERS) + ("adas", "cora", "coni", "sel", "sumz",
                                  "min", "max", "etos", "stoe"))


class ExpressionError(ValueError):
    pass


def real_token(x):
    """A b2plot real: at most 9 digits (b2plot reads the digits as
    integers) and with a point or an exponent, so that it is not read as
    an integer."""
    t = "%.9g" % x
    return t if ("." in t or "e" in t or "n" in t) else t + ".0"


class Translator:
    """kinds: quantity name -> "matrix" or "eirene"; constants: names of
    the b2plot constants."""

    def __init__(self, kinds, constants=()):
        self.kinds, self.constants = kinds, set(constants)

    def __call__(self, text):
        """(b2plot tokens, "matrix" or "eirene") of an expression."""
        try:
            tree = ast.parse(text.strip(), mode="eval").body
        except SyntaxError as err:
            raise ExpressionError("syntax: %s" % err.msg) from None
        words, kind = self._node(tree)
        if kind not in ("matrix", "eirene"):
            raise ExpressionError("the expression gives a number, not a "
                                  "field")
        return " ".join(words), kind

    @staticmethod
    def _op(name, kind):
        """The Eirene stack version of a b2plot operation (rm* rem*,
        m+ em+, zsel ezsel, ...)."""
        if kind != "eirene":
            return name
        return "re" + name[1:] if name.startswith("rm") else "e" + name

    def _node(self, n):
        """(tokens, kind) with kind matrix, eirene, real (value) or str."""
        if isinstance(n, ast.Constant):
            if isinstance(n.value, str):
                return ["'%s'" % n.value], "str"
            if isinstance(n.value, (int, float)):
                return [real_token(n.value)], ("real", float(n.value))
        if isinstance(n, ast.Name):
            if n.id in self.kinds:
                return ["{%s}" % n.id], self.kinds[n.id]
            if n.id in self.constants:
                return [n.id], ("real", None)
            raise ExpressionError("unknown quantity %s" % n.id)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            w, k = self._node(n.operand)
            if isinstance(k, tuple) and k[1] is not None:
                return [real_token(-k[1])], ("real", -k[1])
            return w + [self._op("chs", self._field(k))], k
        if isinstance(n, ast.BinOp):
            return self._binop(n)
        if isinstance(n, ast.Compare) and len(n.ops) == 1:
            return self._compare(n.ops[0], n.left, n.comparators[0])
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            return self._call(n.func.id, n.args)
        raise ExpressionError("not understood: %s" % ast.unparse(n))

    @staticmethod
    def _field(kind):
        if kind not in ("matrix", "eirene"):
            raise ExpressionError("a field is needed here")
        return kind

    def _binop(self, n):
        a, ka = self._node(n.left)
        b, kb = self._node(n.right)
        op = type(n.op)
        if isinstance(ka, tuple) and isinstance(kb, tuple):
            if ka[1] is None or kb[1] is None:
                raise ExpressionError("constants only on fields")
            v = {ast.Add: ka[1] + kb[1], ast.Sub: ka[1] - kb[1],
                 ast.Mult: ka[1] * kb[1], ast.Pow: ka[1] ** kb[1],
                 ast.Div: ka[1] / kb[1] if kb[1] else None}.get(op)
            if v is None:
                raise ExpressionError("not a number: %s" % ast.unparse(n))
            return [real_token(v)], ("real", v)
        if isinstance(kb, tuple):               # field op real
            if op not in REAL_OPS:
                raise ExpressionError("not understood: %s" % ast.unparse(n))
            k = self._field(ka)
            return a + b + [self._op(REAL_OPS[op], k)], k
        if isinstance(ka, tuple):               # real op field
            k = self._field(kb)
            if op in (ast.Add, ast.Mult):
                return b + a + [self._op(REAL_OPS[op], k)], k
            if op is ast.Sub:
                return b + [self._op("chs", k)] + a + [self._op("rm+", k)], k
            if op is ast.Div:
                return b + ["-1.0", self._op("rm**", k)] + a \
                    + [self._op("rm*", k)], k
            raise ExpressionError("a number to the power of a field")
        if ka != kb:
            raise ExpressionError("B2.5 and Eirene fields mixed: convert "
                                  "with etos() or stoe()")
        if op not in FIELD_OPS:
            raise ExpressionError("field to the power of a field")
        return a + b + [self._op(FIELD_OPS[op], self._field(ka))], ka

    def _compare(self, op, left, right):
        a, ka = self._node(left)
        b, kb = self._node(right)
        if isinstance(ka, tuple) and not isinstance(kb, tuple):
            a, ka, b, kb, op = b, kb, a, ka, MIRROR[type(op)]()
        if not isinstance(kb, tuple):
            raise ExpressionError("compare a field with a number")
        k = self._field(ka)
        return a + b + [self._op(COMPARE[type(op)], k)], k

    def _ints(self, args, n, name):
        if len(args) != n or not all(isinstance(a, ast.Constant)
                                     and isinstance(a.value, int)
                                     for a in args):
            raise ExpressionError("%s needs %d integers" % (name, n))
        return [str(a.value) for a in args]

    def _call(self, name, args):
        if name in self.kinds:              # label with an integer argument
            return self._ints(args, 1, name) + [name], self.kinds[name]
        if name in UNARY + MATRIX_ONLY + EIRENE_ONLY + ("etos", "stoe"):
            if len(args) != 1:
                raise ExpressionError("%s takes one field" % name)
            w, k = self._node(args[0])
            k = self._field(k)
            if (name in MATRIX_ONLY + ("stoe",) and k != "matrix") or \
                    (name in EIRENE_ONLY + ("etos",) and k != "eirene"):
                raise ExpressionError("%s does not take this field" % name)
            out = {"etos": "matrix", "stoe": "eirene"}.get(name, k)
            fn = name if name not in UNARY else self._op(name, k)
            return w + [fn], out
        if name in ("sel", "sumz"):
            w, k = self._node(args[0]) if args else ([], None)
            k = self._field(k)
            ints = self._ints(args[1:], 1 if name == "sel" else 2, name)
            fn = {"sel": "zsel", "sumz": "sumz"}[name]
            return w + ints + [self._op(fn, k)], k
        if name in ("min", "max"):
            if len(args) != 2:
                raise ExpressionError("%s takes two fields" % name)
            (a, ka), (b, kb) = self._node(args[0]), self._node(args[1])
            if ka != kb or ka not in ("matrix", "eirene"):
                raise ExpressionError("%s takes two fields of one kind"
                                      % name)
            return a + b + [self._op("m" + name[:3], ka)], ka
        if name in FITS:
            kind, nfield = FITS[name]
            strings = [self._node(a) for a in args[:4]]
            if len(args) < 4 or any(k != "str" for _, k in strings):
                raise ExpressionError("%s needs file, section, reaction, "
                                      "type" % name)
            fields = [self._node(a) for a in args[4:]]
            if len(fields) > nfield or not (nfield == 0 or fields) or \
                    any(k != kind for _, k in fields):
                raise ExpressionError("%s takes %s %s field(s)" % (
                    name, "1 or 2" if nfield else "no", kind))
            return sum((w for w, _ in fields), []) + sum(
                (w for w, _ in strings), []) + [name], kind
        if name in INTEGERS:
            return self._ints(args, INTEGERS[name], name) + [name], "matrix"
        if name == "adas":
            if len(args) != 1 or self._node(args[0])[1] != "str":
                raise ExpressionError("adas needs one string")
            return self._node(args[0])[0] + ["adas"], "matrix"
        if name in ("cora", "coni") and not args:
            return [name], "matrix"
        raise ExpressionError("unknown function %s" % name)


def names_of(tokens):
    """Quantity names {name} in translated tokens."""
    return set(re.findall(r"\{([^}]+)\}", tokens))
