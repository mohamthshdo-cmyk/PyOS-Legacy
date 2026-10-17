"""App commands: launch, apps, kill."""
import os
import platform


def _reg():
    """Import REGISTRY lazily to avoid circular imports at load time."""
    from pyos.apps import REGISTRY
    return REGISTRY


def apps_list(sh, args, line):
    reg = _reg()
    sh.info(str(len(reg)) + " app(s) available:")
    for k in sorted(reg.keys()):
        sh.writeln("  " + k.ljust(14) + reg[k]["name"])


def launch(sh, args, line):
    if not args:
        return sh.err("usage: launch <app-name>   (see 'apps' for list)")
    name = args[0]
    reg = _reg()
    if name not in reg:
        return sh.err("launch: no app named '" + name + "'")
    try:
        from pyos.kernel.state import STATE
    except Exception:
        return sh.err("launch: state unavailable")
    if STATE.desktop is None:
        return sh.err("launch: desktop not available")
    STATE.desktop.open_app(name)
    sh.ok("Launched " + name)


def kill(sh, args, line):
    if not args:
        return sh.err("usage: kill <pid>")
    for t in args:
        try:
            pid = int(t)
            if platform.system() == "Windows":
                os.system("taskkill /F /PID " + str(pid) + " >nul 2>&1")
            else:
                os.kill(pid, 9)
            sh.ok("killed pid " + str(pid))
        except Exception as e:
            sh.err("kill: " + str(e))


COMMANDS = {
    "apps":   (apps_list, "list available apps",           "Apps"),
    "launch": (launch,    "launch an app by name",         "Apps"),
    "kill":   (kill,      "terminate a process by PID",    "Apps"),
}
