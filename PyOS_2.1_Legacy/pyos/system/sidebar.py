"""Left vertical dock - one icon per app."""
import tkinter as tk
import datetime


class Sidebar:
    WIDTH = 72

    def __init__(self, desktop, on_launcher, apps_dict):
        """
        apps_dict : dict { key: {"name":..., "icon":..., "class":...} }
                    Only one icon per key is ever created.
        """
        self.desktop = desktop
        self.frame = tk.Frame(desktop.root, bg="#16161e", width=self.WIDTH)
        self.frame.pack(side="left", fill="y")
        self.frame.pack_propagate(False)

        tk.Frame(self.frame, bg="#7aa2f7", height=3).pack(fill="x")

        tk.Button(self.frame, text="\u2630", font=("Segoe UI", 14),
                  bg="#16161e", fg="#7aa2f7", bd=0,
                  activebackground="#1f2335",
                  command=on_launcher).pack(pady=(10, 6), ipadx=8, ipady=4)

        tk.Frame(self.frame, bg="#2a2e3f", height=1).pack(fill="x", padx=10)

        # Scrollable container for app icons
        wrap = tk.Frame(self.frame, bg="#16161e")
        wrap.pack(fill="both", expand=False, pady=(6, 0))

        self.canvas = tk.Canvas(wrap, bg="#16161e", highlightthickness=0,
                                width=self.WIDTH - 6)
        self.canvas.pack(side="left", fill="y", expand=True)

        self.apps_frame = tk.Frame(self.canvas, bg="#16161e")
        self.canvas.create_window((0, 0), window=self.apps_frame, anchor="nw")

        def _resize(e=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.apps_frame.bind("<Configure>", _resize)
        self.canvas.bind("<MouseWheel>",
                         lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        tk.Frame(self.frame, bg="#16161e").pack(expand=True, fill="y")
        tk.Frame(self.frame, bg="#2a2e3f", height=1).pack(fill="x", padx=10)

        self.clock = tk.Label(self.frame, text="", bg="#16161e", fg="#c0caf5",
                              font=("Segoe UI", 8), justify="center")
        self.clock.pack(pady=8)
        self._tick()

        tk.Button(self.frame, text="\u23FB", font=("Segoe UI", 12),
                  bg="#16161e", fg="#f7768e", bd=0,
                  activebackground="#1f2335",
                  command=self._power).pack(pady=(0, 10))

        # Add every app in the registry, ONCE each.
        self.buttons = {}
        for key in sorted(apps_dict.keys()):
            meta = apps_dict[key]
            self._add_icon(key, meta)

    def _tick(self):
        now = datetime.datetime.now()
        self.clock.config(text=now.strftime("%H:%M\n%d %b"))
        self.frame.after(1000, self._tick)

    def _add_icon(self, key, meta):
        if key in self.buttons:
            return  # never duplicate
        b = tk.Button(self.apps_frame,
                      text=meta.get("icon", "?"),
                      font=("Segoe UI", 14),
                      bg="#1f2335", fg="#c0caf5", bd=0,
                      activebackground="#2a2e3f", activeforeground="#7aa2f7",
                      command=lambda k=key: self.desktop.open_app(k))
        b.pack(pady=3, padx=4, ipadx=8, ipady=4)
        self.buttons[key] = b

    def _power(self):
        m = tk.Menu(self.frame, tearoff=0, bg="#1f2335", fg="#c0caf5",
                    activebackground="#7aa2f7", activeforeground="#16161e")
        m.add_command(label="  Log out", command=self.desktop.logout)
        m.add_command(label="  Shutdown", command=self.desktop.shutdown)
        try:
            m.tk_popup(self.frame.winfo_rootx(), self.frame.winfo_rooty() + 200)
        finally:
            m.grab_release()
