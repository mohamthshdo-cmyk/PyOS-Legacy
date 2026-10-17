"""Persistent state."""
import os, json, copy

PYOS_HOME = os.path.join(os.path.expanduser("~"), ".pyos")
USERS_FILE = os.path.join(PYOS_HOME, "users.json")
STATE_FILE = os.path.join(PYOS_HOME, "state.json")
try:
    os.makedirs(PYOS_HOME, exist_ok=True)
except OSError as _e:
    print("[state] warning: cannot create " + PYOS_HOME + ": " + str(_e))

DEFAULT_STATE = {
    "hostname": "pyos",
    "packages": ["coreutils", "pysh", "tk", "python3"],
    "first_boot": True,
    "wallpaper": "#1a1b26",
    "version": "2.2.0",
    "boot_count": 0,
}

def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return copy.deepcopy(default) if isinstance(default, dict) else default

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class State:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.users = _load(USERS_FILE, {})
        self.data = _load(STATE_FILE, DEFAULT_STATE)
        for k, v in DEFAULT_STATE.items():
            self.data.setdefault(k, v)
        self.current_user = None
        self.boot_time = None
        self.desktop = None

    def save(self):
        _save(USERS_FILE, self.users)
        _save(STATE_FILE, self.data)

    def log(self, msg):
        try:
            with open(os.path.join(PYOS_HOME, "boot.log"), "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            pass

STATE = State()