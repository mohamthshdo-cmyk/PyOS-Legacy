"""Window manager - windows clamped to the PyOS desktop area."""
import tkinter as tk


class ManagedWindow(tk.Toplevel):
    def __init__(self, wm, title, builder, width=720, height=460, icon="?"):
        super().__init__(wm.root)
        self.wm = wm
        self.title_text = title
        self.icon = icon
        self.minimized = False
        self._drag = {"x": 0, "y": 0}

        self.overrideredirect(True)
        self.configure(bg="#16161e")

        # Initial position inside the desktop area
        n = len(wm.windows)
        x = wm.bounds["x"] + 40 + n * 24
        y = wm.bounds["y"] + 40 + n * 24
        self.geometry(str(width) + "x" + str(height) + "+" + str(x) + "+" + str(y))

        bar = tk.Frame(self, bg="#1f2335", height=32)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text=icon + "  " + title, bg="#1f2335", fg="#c0caf5",
                 font=("Segoe UI", 10)).pack(side="left", padx=10)

        tk.Button(bar, text="X", bg="#1f2335", fg="#f7768e", bd=0,
                  activebackground="#f7768e", activeforeground="#16161e",
                  command=self.close, font=("Segoe UI", 11)
                  ).pack(side="right", padx=4)
        tk.Button(bar, text="[]", bg="#1f2335", fg="#e0af68", bd=0,
                  activebackground="#e0af68", activeforeground="#16161e",
                  command=self.toggle_max, font=("Segoe UI", 11)
                  ).pack(side="right")
        tk.Button(bar, text="-", bg="#1f2335", fg="#9ece6a", bd=0,
                  activebackground="#9ece6a", activeforeground="#16161e",
                  command=self.minimize, font=("Segoe UI", 11)
                  ).pack(side="right")

        self.content = tk.Frame(self, bg="#1a1b26")
        self.content.pack(fill="both", expand=True)
        builder(self.content)

        bar.bind("<ButtonPress-1>", self._start)
        bar.bind("<B1-Motion>", self._move)

    # ---------------- dragging ----------------
    def _start(self, e):
        self._drag["x"], self._drag["y"] = e.x, e.y

    def _move(self, e):
        x = self.winfo_x() + e.x - self._drag["x"]
        y = self.winfo_y() + e.y - self._drag["y"]
        x, y = self._clamp_xy(x, y)
        self.geometry("+" + str(x) + "+" + str(y))

    def _clamp_xy(self, x, y):
        """Keep the window inside the current desktop area."""
        b = self.wm.bounds
        w = self.winfo_width()  or 100
        h = self.winfo_height() or 100
        min_x = b["x"]
        min_y = b["y"]
        max_x = b["x"] + b["w"] - w
        max_y = b["y"] + b["h"] - h
        if max_x < min_x: max_x = min_x
        if max_y < min_y: max_y = min_y
        x = max(min_x, min(x, max_x))
        y = max(min_y, min(y, max_y))
        return x, y

    # ---------------- window controls ----------------
    def minimize(self):
        self.withdraw()
        self.minimized = True

    def restore(self):
        self.deiconify()
        self.minimized = False
        self.lift()

    def close(self):
        self.wm.unregister(self)
        try:
            self.destroy()
        except Exception:
            pass

    def toggle_max(self):
        if hasattr(self, "_restore_geo"):
            self.geometry(self._restore_geo)
            del self._restore_geo
            return
        self._restore_geo = self.geometry()
        b = self.wm.bounds
        self.geometry(str(b["w"]) + "x" + str(b["h"]) + "+" + str(b["x"]) + "+" + str(b["y"]))


class WindowManager:
    def __init__(self, root, sidebar_widget):
        self.root = root
        self.windows = []
        self.sidebar_widget = sidebar_widget
        self.bounds = {"x": 0, "y": 0, "w": 800, "h": 600}
        root.bind("<Configure>",
                  lambda e: self.refresh_bounds() if e.widget is root else None,
                  add="+")

    def refresh_bounds(self):
        """Recompute the desktop area's screen coordinates."""
        self.root.update_idletasks()
        r = self.root
        # sidebar occupies the left
        sx = self.sidebar_widget.frame.winfo_rootx()
        sy = self.sidebar_widget.frame.winfo_rooty()
        sw = self.sidebar_widget.frame.winfo_width()
        # root's screen position and size
        rx = r.winfo_rootx()
        ry = r.winfo_rooty()
        rw = r.winfo_width()
        rh = r.winfo_height()
        # desktop area = everything to the right of the sidebar
        self.bounds = {
            "x": sx + sw,
            "y": ry,
            "w": rx + rw - (sx + sw),
            "h": rh,
        }
        # Re-clamp every open window to the new bounds
        for w in self.windows:
            try:
                x, y = w._clamp_xy(w.winfo_x(), w.winfo_y())
                w.geometry("+" + str(x) + "+" + str(y))
            except Exception:
                pass

    def register_window(self, win):
        self.windows.append(win)

    def unregister(self, win):
        if win in self.windows:
            self.windows.remove(win)

    def open(self, title, builder, w=720, h=460, icon="?"):
        self.refresh_bounds()
        win = ManagedWindow(self, title, builder, w, h, icon=icon)
        self.register_window(win)
        win.lift()
        return win
