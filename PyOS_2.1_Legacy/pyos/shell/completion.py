"""Tab completion for PyShell."""
import os


def complete(shell, line):
    if not line or line[-1] == " ":
        return _command_completions(shell, ""), ""

    i = len(line) - 1
    while i >= 0 and not line[i].isspace():
        i -= 1
    prefix = line[i+1:]
    before = line[:i+1]

    if not before.strip():
        return _command_completions(shell, prefix), prefix

    return _path_completions(prefix), prefix


def _command_completions(shell, prefix):
    names = set(shell.commands.keys())
    names.update(shell.aliases.keys())
    names.update(shell.env.keys())
    names = sorted(names)
    return [n for n in names if n.startswith(prefix)]


def _path_completions(prefix):
    expanded = os.path.expanduser(prefix)
    dirname = os.path.dirname(expanded) or "."
    basename = os.path.basename(expanded)

    try:
        entries = os.listdir(dirname)
    except Exception:
        return []

    matches = []
    for name in entries:
        if not name.startswith(basename):
            continue
        full = os.path.join(dirname, name)
        if prefix.startswith("~"):
            rel = os.path.relpath(full, os.path.expanduser("~"))
            shown = "~/" + rel.replace(os.sep, "/")
        elif not os.path.isabs(prefix):
            shown = os.path.relpath(full, os.getcwd()).replace(os.sep, "/")
            if shown == ".":
                shown = "./"
        else:
            shown = full
        if os.path.isdir(full):
            shown += "/"
        matches.append(shown)
    return sorted(matches)
