"""App registry - lazy, avoids circular imports."""


def _build():
    from pyos.apps.terminal_app import TerminalApp
    from pyos.apps import pychrome as pychrome_mod

    reg = {
        "terminal": {"name": "Terminal", "icon": "T", "class": TerminalApp},
        "pychrome": {"name": "PyChrome", "icon": "C", "class": pychrome_mod.PyChromeApp},
    }

    # Optional apps - add only if the modules exist
    try:
        from pyos.apps import notepad
        reg["notepad"] = {"name": "Notepad", "icon": "N", "class": notepad.NotepadApp}
    except Exception as e:
        print("[apps] notepad not loaded: " + str(e))

    try:
        from pyos.apps import calculator
        reg["calculator"] = {"name": "Calculator", "icon": "C", "class": calculator.CalculatorApp}
    except Exception as e:
        print("[apps] calculator not loaded: " + str(e))

    try:
        from pyos.apps import explorer
        reg["explorer"] = {"name": "File Explorer", "icon": "F", "class": explorer.ExplorerApp}
    except Exception as e:
        print("[apps] explorer not loaded: " + str(e))

    try:
        from pyos.apps import sysmon
        reg["sysmon"] = {"name": "System Monitor", "icon": "M", "class": sysmon.SysMonApp}
    except Exception as e:
        print("[apps] sysmon not loaded: " + str(e))

    return reg


class _Registry:
    def __init__(self):
        self._data = None
    def _ensure(self):
        if self._data is None:
            self._data = _build()
        return self._data
    def __getitem__(self, k):    return self._ensure()[k]
    def __setitem__(self, k, v): self._ensure()[k] = v
    def __delitem__(self, k):    del self._ensure()[k]
    def __contains__(self, k):   return k in self._ensure()
    def __iter__(self):          return iter(self._ensure())
    def __len__(self):           return len(self._ensure())
    def keys(self):              return self._ensure().keys()
    def values(self):            return self._ensure().values()
    def items(self):             return self._ensure().items()
    def get(self, k, d=None):    return self._ensure().get(k, d)


REGISTRY = _Registry()
