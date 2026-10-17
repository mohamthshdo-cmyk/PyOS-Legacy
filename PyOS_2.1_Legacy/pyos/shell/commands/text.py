"""Text tools: grep, head, tail, wc, sort, uniq, cut, tr, sed."""
import os, re


def _lines(sh, args):
    """Read piped stdin if available; else from a file argument."""
    buf = getattr(sh, "_current_stdin", None)
    if buf:
        return buf.splitlines()
    if args and not args[0].startswith("-"):
        try:
            with open(args[0], encoding="utf-8", errors="replace") as f:
                return f.read().splitlines()
        except Exception as e:
            sh.err(str(e))
            return []
    return []


def grep(sh, args, line):
    opts = [a for a in args if a.startswith("-")]
    rest = [a for a in args if not a.startswith("-")]
    if not rest:
        return sh.err("usage: grep [-i] [-v] [-n] pattern [file]")
    pat = rest[0]
    flags = re.IGNORECASE if "-i" in opts else 0
    try:
        rx = re.compile(pat, flags)
    except re.error as e:
        return sh.err("grep: " + str(e))
    inv = "-v" in opts
    num = "-n" in opts
    matched = False
    for i, l in enumerate(_lines(sh, rest[1:]), 1):
        hit = bool(rx.search(l))
        if hit != inv:
            matched = True
            sh.writeln((str(i) + ":" + l) if num else l)
    return 0 if matched else 1


def head(sh, args, line):
    n = 10
    if args and args[0].startswith("-"):
        try: n = int(args[0][1:])
        except: pass
        args = args[1:]
    for l in _lines(sh, args)[:n]:
        sh.writeln(l)


def tail(sh, args, line):
    n = 10
    if args and args[0].startswith("-"):
        try: n = int(args[0][1:])
        except: pass
        args = args[1:]
    for l in _lines(sh, args)[-n:]:
        sh.writeln(l)


def wc(sh, args, line):
    ls = _lines(sh, args)
    nl = len(ls)
    nw = sum(len(l.split()) for l in ls)
    nc = sum(len(l) for l in ls) + nl
    sh.writeln(str(nl).rjust(6) + " " + str(nw).rjust(6) + " " + str(nc).rjust(6))


def sort(sh, args, line):
    for l in sorted(_lines(sh, args)):
        sh.writeln(l)


def uniq(sh, args, line):
    prev = None
    for l in _lines(sh, args):
        if l != prev:
            sh.writeln(l)
        prev = l


def cut(sh, args, line):
    delim, field, rest = "\t", 1, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "-d" and i + 1 < len(args):
            delim = args[i + 1]; i += 2
        elif a.startswith("-d") and len(a) > 2:
            delim = a[2:]; i += 1
        elif a == "-f" and i + 1 < len(args):
            try: field = int(args[i + 1])
            except ValueError: pass
            i += 2
        elif a.startswith("-f") and len(a) > 2:
            try: field = int(a[2:])
            except ValueError: pass
            i += 1
        else:
            rest.append(a); i += 1
    if not delim:
        return sh.err("cut: empty delimiter")
    for l in _lines(sh, rest):
        parts = l.split(delim)
        if 1 <= field <= len(parts):
            sh.writeln(parts[field - 1])

def tr(sh, args, line):
    if len(args) < 2:
        return sh.err("usage: tr <from> <to> [file]")
    if len(args[0]) != len(args[1]):
        return sh.err("tr: from and to must be same length")
    table = str.maketrans(args[0], args[1])
    files = [a for a in args[2:] if not a.startswith("-")]
    for l in _lines(sh, files):
        sh.writeln(l.translate(table))

COMMANDS = {
    "grep": (grep, "search text with regex (-i -v -n)", "Text"),
    "head": (head, "show first N lines (default 10)",   "Text"),
    "tail": (tail, "show last N lines (default 10)",    "Text"),
    "wc":   (wc,   "count lines, words, chars",         "Text"),
    "sort": (sort, "sort lines alphabetically",         "Text"),
    "uniq": (uniq, "remove adjacent duplicate lines",   "Text"),
    "cut":  (cut,  "extract a field (-d delim -f N)",   "Text"),
    "tr":   (tr,   "translate characters",              "Text"),
}