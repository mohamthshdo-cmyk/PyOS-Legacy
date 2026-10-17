"""Terminal widget: prompt, history, ANSI colors, tab completion, PS1."""
import os
import tkinter as tk
from pyos.kernel.state import STATE
from pyos.shell import completion


class Terminal(tk.Text):
    COLORS = {"31": "#f7768e", "32": "#9ece6a", "33": "#e0af68",
              "34": "#7aa2f7", "35": "#bb9af7", "36": "#7dcfff",
              "37": "#c0caf5", "90": "#565f89"}

    def __init__(self, parent, on_command):
        super().__init__(parent, bg="#0c0c0c", fg="#c0caf5",
                         insertbackground="#9ece6a",
                         font=("Consolas", 10), bd=0, wrap="word",
                         selectbackground="#2a2e3f")
        self.on_command = on_command
        self.shell = None
        self.history = []
        self.hist_idx = 0
        self.default_ps1 = None
        for code, color in self.COLORS.items():
            self.tag_configure("c" + code, foreground=color)
        self.bind("<Return>", self._enter)
        self.bind("<Up>", self._up)
        self.bind("<Down>", self._down)
        self.bind("<BackSpace>", self._bs)
        self.bind("<Tab>", self._tab)
        self.bind("<Control-c>", self._ctrl_c)
        self.bind("<Control-l>", self._ctrl_l)
        self.bind("<Control-a>", self._ctrl_a)
        self.bind("<Control-e>", self._ctrl_e)
        self.bind("<Control-u>", self._ctrl_u)
        self.bind("<Control-k>", self._ctrl_k)
        self.bind("<Control-w>", self._ctrl_w)

    def prompt_pos(self):
        line = self.get("insert linestart", "insert lineend")
        # look for the prompt marker "> " (PS1 always ends with that)
        idx = line.rfind("> ")
        if idx == -1:
            idx = line.rfind("$ ")
        if idx == -1:
            return self.index("insert linestart")
        return self.index("insert linestart") + "+" + str(idx + 2) + "c"

    def write_prompt(self):
        ps1 = None
        if self.shell is not None:
            ps1 = self.shell.env.get("PS1")
        if ps1:
            self.insert("end", ps1, "c37")
            self.see("end")
            return

        # default prompt: user@host:cwd>
        user = STATE.current_user or "guest"
        host = STATE.data["hostname"]
        try:
            cwd = os.getcwd()
            home = os.path.expanduser("~")
            if cwd.startswith(home):
                cwd = "~" + cwd[len(home):]
        except Exception:
            cwd = "~"
        self.insert("end", user, "c31" if user == "root" else "c32")
        self.insert("end", "@", "c37")
        self.insert("end", host, "c32")
        self.insert("end", ":", "c37")
        self.insert("end", cwd, "c34")
        self.insert("end", "> ", "c37")
        self.see("end")

    def _bs(self, e):
        if self.compare("insert", "<=", self.prompt_pos()):
            return "break"

    def _enter(self, e):
        line = self.get(self.prompt_pos(), "insert")
        self.insert("end", "\n")
        if line.strip():
            self.history.append(line)
        self.hist_idx = len(self.history)
        self.on_command(line)
        self.write_prompt()
        self.see("end")
        return "break"

    def _up(self, e):
        if not self.history:
            return "break"
        self.hist_idx = max(0, self.hist_idx - 1)
        self._replace(self.history[self.hist_idx])
        return "break"

    def _down(self, e):
        if not self.history:
            return "break"
        self.hist_idx = min(len(self.history), self.hist_idx + 1)
        txt = self.history[self.hist_idx] if self.hist_idx < len(self.history) else ""
        self._replace(txt)
        return "break"

    def _replace(self, text):
        self.delete(self.prompt_pos(), "insert")
        self.insert("end", text)

    def _tab(self, e):
        if self.shell is None:
            return "break"
        line = self.get(self.prompt_pos(), "insert")
        matches, prefix = completion.complete(self.shell, line)
        if not matches:
            return "break"
        if len(matches) == 1:
            self.delete(self.prompt_pos() + "+" + str(len(line) - len(prefix)) + "c", "insert")
            self.insert("end", matches[0])
        else:
            common = os.path.commonprefix(matches)
            if len(common) > len(prefix):
                self.delete(self.prompt_pos() + "+" + str(len(line) - len(prefix)) + "c", "insert")
                self.insert("end", common)
            else:
                self.insert("end", "\n")
                for m in matches:
                    self.insert("end", m + "  ")
                self.insert("end", "\n")
                self.write_prompt()
                self.insert("end", line)
        return "break"

    def _ctrl_c(self, e):
        self.insert("end", "^C\n")
        self.write_prompt()
        return "break"

    def _ctrl_l(self, e):
        self.delete("1.0", "end")
        self.write_prompt()
        return "break"

    def _ctrl_a(self, e):
        self.mark_set("insert", self.prompt_pos())
        return "break"

    def _ctrl_e(self, e):
        self.mark_set("insert", "insert lineend")
        return "break"

    def _ctrl_u(self, e):
        self.delete(self.prompt_pos(), "insert")
        return "break"

    def _ctrl_k(self, e):
        self.delete("insert", "insert lineend")
        return "break"

    def _ctrl_w(self, e):
        # delete word before cursor, but not before prompt
        pos = self.index("insert")
        line = self.get(self.prompt_pos(), pos)
        if not line:
            return "break"
        # strip trailing whitespace, then non-space chars
        s = line.rstrip()
        cut = s.rfind(" ")
        keep = s[:cut+1] if cut != -1 else ""
        self.delete(self.prompt_pos(), "insert")
        self.insert("end", keep)
        return "break"
