"""jobs / fg / bg / kill / wait commands."""


def jobs(sh, args, line):
    jlist = sh.jobs.list()
    if not jlist:
        sh.info("no jobs")
        return
    for j in jlist:
        marker = "+" if j is jlist[-1] else "-"
        sh.writeln("[" + str(j.id) + "]" + marker + "  " + j.state + "    " + j.command)


def kill(sh, args, line):
    if not args:
        return sh.err("usage: kill [-9] <pid> [<pid>...]")
    sig = "-9" if "-9" in args else ""
    pids = [a for a in args if not a.startswith("-")]
    import os, platform
    for p in pids:
        try:
            pid = int(p)
        except ValueError:
            sh.err("kill: invalid pid: " + p)
            continue
        try:
            if platform.system() == "Windows":
                os.system("taskkill /F /PID " + str(pid) + " >nul 2>&1")
            else:
                os.kill(pid, 9 if sig == "-9" else 15)
            sh.ok("killed pid " + str(pid))
        except Exception as e:
            sh.err("kill: " + str(e))


def wait_cmd(sh, args, line):
    import time
    sh.info("waiting for background jobs...")
    for j in sh.jobs.list():
        j.thread.join()
    sh.ok("all jobs done")


def fg(sh, args, line):
    jlist = sh.jobs.list()
    if not jlist:
        return sh.info("no jobs")
    target = None
    if args:
        try:
            jid = int(args[0].lstrip("%"))
            target = sh.jobs.get(jid)
        except ValueError:
            return sh.err("fg: bad job id")
    else:
        target = jlist[-1]
    if not target:
        return sh.err("fg: no such job")
    sh.info("fg: bringing job " + str(target.id) + " to foreground")
    target.thread.join()


def bg(sh, args, line):
    jlist = sh.jobs.list()
    if not jlist:
        return sh.info("no jobs")
    target = jlist[-1]
    if args:
        try:
            target = sh.jobs.get(int(args[0].lstrip("%"))) or target
        except ValueError:
            pass
    sh.info("[" + str(target.id) + "] " + target.command)


COMMANDS = {
    "jobs": (jobs,     "list background jobs",                "Jobs"),
    "kill": (kill,     "terminate a process by PID",          "Jobs"),
    "wait": (wait_cmd, "wait for all background jobs",        "Jobs"),
    "fg":   (fg,       "bring last background job to front",  "Jobs"),
    "bg":   (bg,       "resume a stopped job in background",  "Jobs"),
}
