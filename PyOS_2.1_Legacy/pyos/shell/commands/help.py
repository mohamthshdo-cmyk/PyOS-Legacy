"""Help system with explanations."""
from pyos.kernel import __version__, CODENAME


def _get_commands():
    """Lazy import to avoid circular import at module load time."""
    from pyos.shell.commands import ALL_COMMANDS
    return ALL_COMMANDS


def _get_by_cat():
    from pyos.shell.commands import ALL_BY_CATEGORY
    return ALL_BY_CATEGORY


def help_cmd(sh, args, line):
    all_cmds = _get_commands()

    if args:
        name = args[0]
        if name not in all_cmds:
            return sh.err("help: no such command: " + name)
        fn, desc, cat = all_cmds[name]
        sh.ok(name + "  [" + cat + "]")
        sh.writeln("  " + desc)
        extra = getattr(fn, "__doc__", None)
        if extra:
            for l in extra.strip().splitlines():
                sh.writeln("    " + l.strip())
        return

    by_cat = _get_by_cat()
    sh.ok("PyShell " + __version__ + " (" + CODENAME + ")")
    sh.writeln("")
    sh.writeln("Usage:")
    sh.writeln("  <command> [args...]      run a command")
    sh.writeln("  <cmd1> | <cmd2>          pipe output")
    sh.writeln("  help <command>           show details about a command")
    sh.writeln("  help                     this message")
    sh.writeln("")
    sh.writeln("Categories:")
    for cat in sorted(by_cat.keys()):
        sh.writeln("  " + cat)
        for name, desc in sorted(by_cat[cat]):
            sh.writeln("    " + name.ljust(12) + desc)
        sh.writeln("")


COMMANDS = {
    "help": (help_cmd, "show help for a command", "Help"),
    "?":    (help_cmd, "alias for help",          "Help"),
}
