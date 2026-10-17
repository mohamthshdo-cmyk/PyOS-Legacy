"""env / export / unset / set / alias / unalias / which / echo commands."""
import os
import shutil


def env(sh, args, line):
    for k in sorted(sh.env.keys()):
        sh.writeln(k + "=" + str(sh.env[k]))


def export(sh, args, line):
    if not args:
        return env(sh, args, line)
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            v = v.strip("'").strip('"')
            sh.env[k] = v


def unset(sh, args, line):
    for a in args:
        sh.env.pop(a, None)


def setenv(sh, args, line):
    if len(args) < 2:
        return sh.err("usage: set NAME value")
    sh.env[args[0]] = args[1]


def alias(sh, args, line):
    if not args:
        for k, v in sorted(sh.aliases.items()):
            sh.writeln("alias " + k + "='" + v + "'")
        return
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1)
            v = v.strip("'").strip('"')
            sh.define_alias(k, v)


def unalias(sh, args, line):
    if not args:
        return sh.err("usage: unalias <name>")
    for a in args:
        sh.undefine_alias(a)


def which(sh, args, line):
    if not args:
        return sh.err("usage: which <command>")
    for cmd in args:
        if cmd in sh.commands:
            sh.writeln(cmd + ": shell builtin")
        else:
            p = shutil.which(cmd)
            if p:
                sh.writeln(cmd + ": " + p)
            else:
                sh.err(cmd + ": not found")


def echo(sh, args, line):
    sh.writeln(" ".join(args))


COMMANDS = {
    "env":     (env,     "print environment variables",  "Shell"),
    "export":  (export,  "export NAME=value",            "Shell"),
    "unset":   (unset,   "remove env vars",              "Shell"),
    "set":     (setenv,  "set NAME value",               "Shell"),
    "alias":   (alias,   "show or define aliases",       "Shell"),
    "unalias": (unalias, "remove an alias",              "Shell"),
    "which":   (which,   "locate a command",             "Shell"),
    "echo":    (echo,    "print text",                   "Shell"),
}
