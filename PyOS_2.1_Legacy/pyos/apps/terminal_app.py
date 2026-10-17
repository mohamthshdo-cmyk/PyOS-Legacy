"""Terminal app - runs PyShell with tab completion and startup file."""
from pyos.apps.base import BaseApp
from pyos.shell.terminal import Terminal
from pyos.shell.pysh import PyShell


class TerminalApp(BaseApp):
    NAME = "Terminal"
    ICON = "T"
    WIDTH = 820
    HEIGHT = 520

    def build(self, parent):
        state = {"shell": None}

        def safe_run(line):
            sh = state["shell"]
            if sh is None:
                return
            try:
                sh.run(line)
            except Exception as e:
                term.writeln("pysh: " + str(e), "c31")

        term = Terminal(parent, on_command=safe_run)
        term.pack(fill="both", expand=True, padx=6, pady=6)
        try:
            shell = PyShell(term)
            state["shell"] = shell
            term.shell = shell
        except Exception as e:
            term.insert("end", "pysh failed to start: " + str(e) + "\n", "c31")
            return
        term.insert("end", "PyShell 2.2 - type 'help' for commands\n", "c36")
        try:
            shell.run_startup()
        except Exception:
            pass
        term.write_prompt()
        term.focus_set()