"""System commands: whoami, hostname, uname, neofetch, ps, df, free, date."""
import os, datetime, platform
from pyos.kernel.state import STATE
from pyos.kernel import __version__, CODENAME


def whoami(sh, args, line):
    sh.writeln(STATE.current_user or "guest")


def hostname(sh, args, line):
    if args:
        STATE.data["hostname"] = args[0]
        STATE.save()
        sh.ok("hostname set to " + args[0])
    else:
        sh.writeln(STATE.data["hostname"])


def uname(sh, args, line):
    u = platform.uname()
    if args and args[0] == "-a":
        sh.writeln("PyOS " + u.system + " " + u.release + " " + u.machine + " pysh")
    else:
        sh.writeln("PyOS")


def date(sh, args, line):
    sh.writeln(datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y"))


def uptime(sh, args, line):
    if STATE.boot_time:
        delta = datetime.datetime.now() - STATE.boot_time
        sh.writeln("up " + str(delta).split(".")[0])
    else:
        sh.writeln("up unknown")


def ps(sh, args, line):
    sh.writeln("  PID  USER      CMD")
    sh.writeln("  1    root      /sbin/init")
    sh.writeln("  42   root      pysh")
    sh.writeln("  " + str(os.getpid()).ljust(5) + (STATE.current_user or "guest").ljust(10) + "python main.py")


def df(sh, args, line):
    try:
        import shutil
        total, used, free = shutil.disk_usage(os.path.expanduser("~"))
        def h(b): return str(b // (1024**3)) + "G"
        sh.writeln("Filesystem".ljust(20) + "Size".rjust(8) + "Used".rjust(8) + "Avail".rjust(8) + "Use%".rjust(6) + "  Mounted")
        sh.writeln("C:".ljust(20) + h(total).rjust(8) + h(used).rjust(8) + h(free).rjust(8) + ("%.0f%%" % (used/total*100)).rjust(6) + "  /")
    except Exception as e:
        sh.err("df: " + str(e))


def free(sh, args, line):
    try:
        import psutil
        m = psutil.virtual_memory()
        tot = m.total // (1024*1024)
        used = m.used // (1024*1024)
        free_m = m.available // (1024*1024)
        sh.writeln("".ljust(14) + "total".rjust(10) + "used".rjust(10) + "free".rjust(10))
        sh.writeln("Mem:".ljust(14) + str(tot).rjust(10) + str(used).rjust(10) + str(free_m).rjust(10))
    except ImportError:
        sh.info("install psutil for real numbers:  pip install psutil")


def neofetch(sh, args, line):
    user = STATE.current_user or "guest"
    host = STATE.data["hostname"]
    sh.ok("       " + user + "@" + host)
    sh.writeln("       " + "-" * (len(user) + len(host) + 1))
    sh.writeln("   ##  OS: PyOS " + __version__ + " (" + CODENAME + ")")
    sh.writeln("   ##  Kernel: PyOS-native")
    sh.writeln("   ##  Shell: pysh")
    sh.writeln("   ##  Python: " + platform.python_version())
    sh.writeln("   ##  Boot: #" + str(STATE.data["boot_count"]))


def shutdown(sh, args, line):
    sh.writeln("Shutting down PyOS...")
    if STATE.desktop:
        STATE.desktop.shutdown()
    else:
        import sys; sys.exit(0)


def logout(sh, args, line):
    sh.writeln("Logging out...")
    if STATE.desktop:
        STATE.desktop.logout()


COMMANDS = {
    "whoami":   (whoami,   "print current user name",       "System"),
    "hostname": (hostname, "show or set the hostname",      "System"),
    "uname":    (uname,    "print system information (-a)", "System"),
    "date":     (date,     "print current date and time",   "System"),
    "uptime":   (uptime,   "show how long PyOS has been up","System"),
    "ps":       (ps,       "list running processes",        "System"),
    "df":       (df,       "show disk space usage",         "System"),
    "free":     (free,     "show memory usage",             "System"),
    "neofetch": (neofetch, "print system summary",          "System"),
    "shutdown": (shutdown, "shut down PyOS",                "System"),
    "logout":   (logout,   "log out to login screen",       "System"),
}