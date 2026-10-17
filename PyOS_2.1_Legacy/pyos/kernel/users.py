"""User accounts."""
import hashlib, secrets, datetime
from pyos.kernel.state import STATE

def hash_pw(pw, salt=None):
    if salt is None:
        salt = secrets.token_hex(8)
    return salt + "$" + hashlib.sha256((salt + pw).encode()).hexdigest()

def verify_pw(pw, stored):
    if "$" not in stored:
        return False
    salt = stored.split("$", 1)[0]
    return hash_pw(pw, salt) == stored

def add_user(name, pw):
    if name in STATE.users:
        raise ValueError("user '" + name + "' already exists")
    STATE.users[name] = {
        "password": hash_pw(pw),
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    STATE.save()

def verify_user(name, pw):
    u = STATE.users.get(name)
    return bool(u) and verify_pw(pw, u["password"])

def list_users():
    return list(STATE.users.keys())