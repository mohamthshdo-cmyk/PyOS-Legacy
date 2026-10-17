"""TTY boot + login, then desktop."""
import tkinter as tk
import traceback
from pyos.kernel.state import STATE
from pyos.kernel.users import verify_user, list_users, add_user
from pyos.kernel import __version__, CODENAME


BOOT_LINES = [
    ("dim", "[    0.000000] PyOS kernel " + __version__ + " (" + CODENAME + ") booting..."),
    ("dim", "[    0.000118] Command line: BOOT_IMAGE=/boot/pyos rw quiet"),
    ("dim", "[    0.003402] BIOS-provided physical RAM map:"),
    ("dim", "[    0.018293] tmpfs: mounted /run"),
    ("ok",  "[  OK  ] Reached target Basic System."),
    ("ok",  "[  OK  ] Loaded Kernel Modules."),
    ("ok",  "[  OK  ] Mounted Virtual Filesystem."),
    ("ok",  "[  OK  ] Started User Login Management."),
    ("ok",  "[  OK  ] Started PyShell service."),
    ("ok",  "[  OK  ] Reached target Graphical Interface."),
    ("dim", "[    0.612004] PyOS " + __version__ + " ready."),
]


class BootSequence:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyOS tty1")
        self.root.geometry("900x560")
        self.root.configure(bg="#0c0c0c")
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self._center()

        self.text = tk.Text(self.root, bg="#0c0c0c", fg="#c0c0c0",
                            insertbackground="#00ff88", bd=0,
                            font=("Consolas", 10), wrap="word",
                            highlightthickness=0)
        self.text.pack(fill="both", expand=True, padx=16, pady=12)

        for tag, color in [("ok", "#9ece6a"), ("err", "#f7768e"),
                           ("warn", "#e0af68"), ("info", "#7dcfff"),
                           ("dim", "#565f89"), ("prompt", "#c0caf5")]:
            self.text.tag_configure(tag, foreground=color)

        self.text.bind("<Key>", self._block)
        self.buffer = ""
        self.callback = None
        self.i = 0
        self.pending_user = None

    def _center(self):
        self.root.update_idletasks()
        w, h = 900, 560
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(str(w) + "x" + str(h) + "+" + str(x) + "+" + str(y))

    def _quit(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def _block(self, e):
        return "break"

    def start(self):
        self.root.after(150, self._step)
        self.root.mainloop()

    # ---------------- boot phase ----------------
    def _step(self):
        if self.i >= len(BOOT_LINES):
            self.root.after(400, self._login_start)
            return
        tag, line = BOOT_LINES[self.i]
        self.text.insert("end", line + "\n", tag)
        self.text.see("end")
        self.i += 1
        self.root.after(110, self._step)

    # ---------------- login phase ----------------
    def _login_start(self):
        self.text.insert("end", "\nPyOS " + __version__ + " (" + CODENAME + ") tty1\n\n", "info")
        self.text.see("end")
        users = list_users()
        if not users:
            self.text.insert("end", "No users. First-boot setup.\n\n", "warn")
            self._prompt("New username: ", self._new_user_name)
        else:
            self._prompt("pyos login: ", self._login_name)

    def _prompt(self, prompt, callback):
        self.text.insert("end", prompt, "prompt")
        self.text.see("end")
        self.text.focus_set()
        self.buffer = ""
        self.callback = callback
        self.text.unbind("<Key>")
        self.text.bind("<Key>", self._on_key)
        self.text.bind("<Return>", self._on_enter)

    def _on_key(self, e):
        if e.keysym == "Return":
            self._on_enter(e)
            return "break"
        if e.char and e.char.isprintable():
            self.text.insert("end", e.char, "prompt")
            self.buffer += e.char
            self.text.see("end")
        elif e.keysym == "BackSpace" and self.buffer:
            self.buffer = self.buffer[:-1]
            self.text.delete("end-2c", "end-1c")
        return "break"

    def _on_enter(self, e):
        value = self.buffer
        self.text.insert("end", "\n")
        self.buffer = ""
        self.text.unbind("<Key>")
        self.text.bind("<Key>", self._block)
        self.text.unbind("<Return>")
        cb = self.callback
        self.callback = None
        if cb:
            self.root.after(60, lambda: cb(value))
        return "break"

    # ---------------- login flows ----------------
    def _new_user_name(self, name):
        name = name.strip()
        if not name:
            self.text.insert("end", "Name required.\n", "err")
            self._prompt("New username: ", self._new_user_name)
            return
        self.pending_user = name
        self._prompt("New password: ", self._new_user_pw)

    def _new_user_pw(self, pw):
        if not pw:
            self.text.insert("end", "Password required.\n", "err")
            self._prompt("New password: ", self._new_user_pw)
            return
        try:
            add_user(self.pending_user, pw)
            STATE.data["first_boot"] = False
            STATE.save()
            self.text.insert("end", "\nUser created.\n", "ok")
            self.root.after(400, lambda: self._enter_desktop(self.pending_user))
        except Exception as e:
            self.text.insert("end", "Error: " + str(e) + "\n", "err")
            self.root.after(300, self._login_start)

    def _login_name(self, name):
        name = name.strip()
        if name not in list_users():
            self.text.insert("end", "Login incorrect\n\n", "err")
            self.root.after(200, self._login_start)
            return
        self.pending_user = name
        self._prompt("Password: ", self._login_pw)

    def _login_pw(self, pw):
        if verify_user(self.pending_user, pw):
            self.text.insert("end", "\nWelcome to PyOS.\n", "ok")
            self.root.after(400, lambda: self._enter_desktop(self.pending_user))
        else:
            self.text.insert("end", "Login incorrect\n\n", "err")
            self.root.after(200, self._login_start)

    # ---------------- transition to desktop ----------------
    def _enter_desktop(self, username):
        STATE.current_user = username
        STATE.save()

        try:
            self.root.destroy()
        except Exception:
            pass

        try:
            from pyos.system.desktop import Desktop
            Desktop().run()
        except Exception:
            # Print to the parent console
            print("=== DESKTOP FAILED TO START ===")
            traceback.print_exc()
            # Also show a popup so it's visible even if launched with .pyw
            try:
                err_win = tk.Tk()
                err_win.title("PyOS - desktop error")
                err_win.geometry("720x420")
                err_win.configure(bg="#1a1b26")
                t = tk.Text(err_win, bg="#0c0c0c", fg="#f7768e",
                            font=("Consolas", 10), bd=0)
                t.pack(fill="both", expand=True)
                t.insert("end", "Desktop crashed:\n\n")
                t.insert("end", traceback.format_exc())
                err_win.mainloop()
            except Exception:
                pass
