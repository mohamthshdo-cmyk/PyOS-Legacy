"""PyShell - parser + executor + env + aliases + globs + PS1 + pyshrc
             + command substitution + arithmetic + history expansion."""
import os
import re
import glob as globmod
from pyos.shell.commands import ALL_COMMANDS
from pyos.shell import executor
from pyos.shell.jobs import JobManager


class PyShell:
    def __init__(self, terminal):
        self.t = terminal
        self.commands = {name: entry[0] for name, entry in ALL_COMMANDS.items()}
        self._current_stdin = ""
        self.last_exit = 0
        self.aliases = {}
        self.env = self._default_env()
        self.startup_file = os.path.expanduser("~/.pyshrc")
        self.jobs = JobManager(self)

    def _default_env(self):
        import getpass
        try:
            user = getpass.getuser()
        except Exception:
            user = "guest"
        return {
            "USER": user,
            "HOME": os.path.expanduser("~"),
            "PWD": os.getcwd(),
            "SHELL": "/bin/pysh",
            "PATH": "/usr/bin:/bin",
            "TERM": "pysh",
        }

    # ---------------- IO ----------------
    def write(self, text, tag=None):
        self.t.insert("end", text, tag)

    def writeln(self, text="", tag=None):
        self.write(text + "\n", tag)

    def err(self, text):
        self.writeln(text, "c31")

    def ok(self, text):
        self.writeln(text, "c32")

    def info(self, text):
        self.writeln(text, "c36")

    # ---------------- top-level ----------------
    def run(self, line):
        line = line.strip()
        if not line or line.startswith("#"):
            return
        self.env["PWD"] = os.getcwd()

        line = self._expand_history(line)
        line = self._expand_substitutions(line)
        line = self._expand_arithmetic(line)
        line = self._expand_vars(line)
        line = self._expand_aliases(line)
        line = self._expand_globs(line)

        # detect trailing & for background
        is_bg = line.endswith("&") and not line.endswith("&&")
        if is_bg:
            line = line[:-1].rstrip()

        if is_bg:
            self._run_background(line)
            self.env["?"] = str(self.last_exit)
            return

        try:
            executor.execute(self, line)
        except Exception as e:
            self.err("pysh: " + str(e))
        self.env["?"] = str(self.last_exit)

    # ---------------- history expansion ----------------
    def _expand_history(self, line):
        # !! = last command
        if line.strip() == "!!":
            hist = getattr(self.t, "history", [])
            if not hist:
                self.err("pysh: !!: event not found")
                return ""
            last = hist[-1]
            self.info(last)
            return last

        # !n  or  !string
        m = re.match(r"^!(\d+|[A-Za-z_][\w]*)\s*(.*)$", line)
        if not m:
            return line
        token, rest = m.group(1), m.group(2)
        hist = getattr(self.t, "history", [])
        if not hist:
            self.err("pysh: !" + token + ": event not found")
            return ""
        if token.isdigit():
            idx = int(token) - 1
            if idx < 0 or idx >= len(hist):
                self.err("pysh: !" + token + ": event not found")
                return ""
            chosen = hist[idx]
        else:
            chosen = None
            for h in reversed(hist):
                if h.startswith(token):
                    chosen = h
                    break
            if chosen is None:
                self.err("pysh: !" + token + ": event not found")
                return ""
        self.info(chosen)
        return chosen + (" " + rest if rest else "")

    # ---------------- command substitution ----------------
    def _expand_substitutions(self, line):
        # find $( ... ) with nesting support; avoid single-quoted regions
        out = []
        i = 0
        n = len(line)
        in_single = False
        while i < n:
            c = line[i]
            if c == "'" and (i == 0 or line[i-1] != "\\"):
                in_single = not in_single
                out.append(c); i += 1; continue
            if c == "$" and not in_single and i + 1 < n and line[i+1] == "(":
                # could be $(( for arithmetic - handled separately
                if i + 2 < n and line[i+2] == "(":
                    out.append(c); i += 1; continue
                # find matching )
                depth = 1
                j = i + 2
                inner = []
                in_q = None
                while j < n and depth > 0:
                    ch = line[j]
                    if in_q:
                        if ch == in_q:
                            in_q = None
                        inner.append(ch)
                    else:
                        if ch in ("'", '"'):
                            in_q = ch
                            inner.append(ch)
                        elif ch == "(":
                            depth += 1
                            inner.append(ch)
                        elif ch == ")":
                            depth -= 1
                            if depth > 0:
                                inner.append(ch)
                        else:
                            inner.append(ch)
                    j += 1
                if depth != 0:
                    # unmatched - leave literal
                    out.append(line[i:i+2]); i += 2; continue
                inner_cmd = "".join(inner)
                try:
                    captured = self._capture_output(inner_cmd)
                except Exception as e:
                    captured = ""
                    self.err("$(...): " + str(e))
                out.append(captured.rstrip("\n"))
                i = j
                continue
            out.append(c)
            i += 1
        return "".join(out)

    def _capture_output(self, cmd_line):
        """Run cmd_line via the executor, capture stdout as a string."""
        buf = []
        orig_write = self.write
        orig_writeln = self.writeln
        orig_ok = self.ok
        orig_info = self.info
        orig_err = self.err

        def cap_write(text, tag=None):
            if tag is None:
                buf.append(text)
            elif tag == "c31":
                # stderr goes to terminal
                orig_write(text, tag)
            else:
                buf.append(text)

        def cap_writeln(text="", tag=None):
            cap_write(text + "\n", tag)

        def cap_ok(text): cap_write(text + "\n", "c32")
        def cap_info(text): cap_write(text + "\n", "c36")
        def cap_err(text):
            orig_err(text)

        self.write = cap_write
        self.writeln = cap_writeln
        self.ok = cap_ok
        self.info = cap_info
        self.err = cap_err
        try:
            executor.execute(self, cmd_line)
        finally:
            self.write = orig_write
            self.writeln = orig_writeln
            self.ok = orig_ok
            self.info = orig_info
            self.err = orig_err
        return "".join(buf)

    # ---------------- arithmetic ----------------
    def _expand_arithmetic(self, line):
        # $(( ... )) -> number
        pattern = re.compile(r"\$\(\((.+?)\)\)")
        def repl(m):
            expr = m.group(1)
            try:
                # evaluate with a clean namespace
                val = eval(expr, {"__builtins__": {}}, {})
                return str(val)
            except Exception:
                return m.group(0)
        return pattern.sub(repl, line)

    # ---------------- env vars ----------------
    def _expand_vars(self, line):
        out = []
        i = 0
        n = len(line)
        in_single = False
        in_double = False
        while i < n:
            c = line[i]
            if c == "'" and not in_double:
                in_single = not in_single; out.append(c); i += 1; continue
            if c == '"' and not in_single:
                in_double = not in_double; out.append(c); i += 1; continue
            if c == "$" and not in_single:
                # don't match $(
                if i + 1 < n and line[i+1] == "(":
                    out.append(c); i += 1; continue
                m = re.match(r"\$\{(\w+|\?|\$)\}|\$(\w+|\?|\$)", line[i:])
                if m:
                    name = m.group(1) or m.group(2)
                    if name == "?":
                        val = str(self.last_exit)
                    elif name == "$":
                        import os as _os
                        val = str(_os.getpid())
                    else:
                        val = self.env.get(name, "")
                    out.append(val)
                    i += m.end()
                    continue
            out.append(c)
            i += 1
        return "".join(out)

    # ---------------- aliases ----------------
    def _expand_aliases(self, line):
        if not self.aliases:
            return line
        parts = line.split(None, 1)
        if not parts:
            return line
        head = parts[0]
        if head in self.aliases:
            tail = parts[1] if len(parts) > 1 else ""
            return self.aliases[head] + (" " + tail if tail else "")
        return line

    # ---------------- globbing ----------------
    def _expand_globs(self, line):
        tokens = []
        buf = []
        in_single = False
        in_double = False
        for c in line:
            if c == "'" and not in_double:
                in_single = not in_single; buf.append(c); continue
            if c == '"' and not in_single:
                in_double = not in_double; buf.append(c); continue
            if c.isspace() and not in_single and not in_double:
                if buf:
                    tokens.append("".join(buf)); buf = []
                continue
            buf.append(c)
        if buf:
            tokens.append("".join(buf))
        out = []
        for tok in tokens:
            if ("*" in tok or "?" in tok) and "'" not in tok and '"' not in tok:
                matches = globmod.glob(os.path.expanduser(tok))
                if matches:
                    out.extend(matches)
                else:
                    out.append(tok)
            else:
                out.append(tok)
        return " ".join(out)

    # ---------------- aliases API ----------------
    def define_alias(self, name, value):
        self.aliases[name] = value

    def undefine_alias(self, name):
        self.aliases.pop(name, None)

    # ---------------- startup ----------------
    def run_startup(self):
        if not os.path.isfile(self.startup_file):
            return
        try:
            with open(self.startup_file, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    self.run(line)
        except Exception as e:
            self.err("pyshrc: " + str(e))

    # ---------------- background ----------------
    def _run_background(self, line):
        def _task():
            try:
                executor.execute(self, line)
            except Exception as e:
                self.err("[bg] " + str(e))
        job = self.jobs.add(line, _task)
        self.info("[" + str(job.id) + "] running in background")
