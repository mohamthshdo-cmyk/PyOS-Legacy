"""Calculator."""
import ast
import operator as _op
import tkinter as tk
from pyos.apps.base import BaseApp

_OPS = {
    ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul,
    ast.Div: _op.truediv, ast.Mod: _op.mod, ast.Pow: _op.pow,
    ast.USub: _op.neg, ast.UAdd: _op.pos,
}

def _safe_eval(expr):
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError("bad expression")
    return _eval(ast.parse(expr, mode="eval").body)


class CalculatorApp(BaseApp):
    NAME = "Calculator"
    ICON = "C"
    WIDTH = 340
    HEIGHT = 460

    def build(self, parent):
        disp = tk.Entry(parent, font=("Segoe UI", 22), bg="#1a1b26",
                        fg="#c0caf5", bd=0, justify="right",
                        insertbackground="#7aa2f7")
        disp.pack(fill="x", padx=10, pady=10, ipady=12)

        def press(v):
            if v == "=":
                try:
                    r = str(_safe_eval(disp.get().replace("x", "*")))
                    disp.delete(0, "end"); disp.insert(0, r)
                except Exception:
                    disp.delete(0, "end"); disp.insert(0, "Error")
            elif v == "C":
                disp.delete(0, "end")
            elif v == "<":
                cur = disp.get()
                if cur:
                    disp.delete(len(cur) - 1, "end")
            else:
                disp.insert("end", v)

        grid = tk.Frame(parent, bg="#1a1b26")
        grid.pack(fill="both", expand=True, padx=10, pady=10)
        rows = [["C", "(", ")", "/"],
                ["7", "8", "9", "x"],
                ["4", "5", "6", "-"],
                ["1", "2", "3", "+"],
                ["0", ".", "<", "="]]
        for r, row in enumerate(rows):
            for c, v in enumerate(row):
                tk.Button(grid, text=v, font=("Segoe UI", 14),
                          bg="#24283b", fg="#c0caf5", bd=0,
                          command=lambda vv=v: press(vv)
                          ).grid(row=r, column=c, sticky="nsew",
                                 padx=3, pady=3, ipady=10)
        for i in range(4):
            grid.columnconfigure(i, weight=1)
        for i in range(5):
            grid.rowconfigure(i, weight=1)