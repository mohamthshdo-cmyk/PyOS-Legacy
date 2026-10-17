"""Notepad."""
import tkinter as tk
from tkinter import filedialog
from pyos.apps.base import BaseApp


class NotepadApp(BaseApp):
    NAME = "Notepad"
    ICON = "N"
    WIDTH = 720
    HEIGHT = 500

    def build(self, parent):
        txt = tk.Text(parent, bg="#1a1b26", fg="#c0caf5",
                      insertbackground="#7aa2f7", font=("Consolas", 11),
                      bd=0, wrap="word")
        txt.pack(fill="both", expand=True, padx=6, pady=6)
        txt.insert("1.0", "Welcome to PyOS Notepad!\n")

        bar = tk.Frame(parent, bg="#1f2335")
        bar.pack(fill="x", side="bottom")

        def save():
            p = filedialog.asksaveasfilename(defaultextension=".txt")
            if p:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(txt.get("1.0", "end-1c"))

        def openf():
            p = filedialog.askopenfilename()
            if p:
                with open(p, encoding="utf-8") as f:
                    txt.delete("1.0", "end")
                    txt.insert("1.0", f.read())

        tk.Button(bar, text="Open", command=openf, bg="#2a2e3f",
                  fg="#c0caf5", bd=0, padx=12, pady=6).pack(side="left", padx=6, pady=6)
        tk.Button(bar, text="Save", command=save, bg="#2a2e3f",
                  fg="#c0caf5", bd=0, padx=12, pady=6).pack(side="left")