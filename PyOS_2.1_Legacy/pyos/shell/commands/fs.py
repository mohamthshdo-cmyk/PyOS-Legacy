"""Filesystem commands: ls, cd, pwd, cat, mkdir, touch, rm, cp, mv, echo."""
import os, shutil


def _r(p):
    return os.path.abspath(os.path.expanduser(p))


def ls(sh, args, line):
    path = _r(args[0]) if args else "."
    try:
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if os.path.isdir(full):
                sh.write(name + "/  ", "c34")
            else:
                sh.write(name + "  ")
        sh.writeln()
    except Exception as e:
        sh.err("ls: " + str(e))


def cd(sh, args, line):
    target = args[0] if args else os.path.expanduser("~")
    try:
        os.chdir(_r(target))
    except Exception as e:
        sh.err("cd: " + str(e))


def pwd(sh, args, line):
    sh.writeln(os.getcwd())


def cat(sh, args, line):
    if not args:
        return sh.err("usage: cat <file>")
    try:
        with open(_r(args[0]), encoding="utf-8", errors="replace") as f:
            sh.writeln(f.read())
    except Exception as e:
        sh.err("cat: " + str(e))


def mkdir(sh, args, line):
    if not args:
        return sh.err("usage: mkdir <dir>")
    try:
        os.makedirs(_r(args[0]), exist_ok=True)
    except Exception as e:
        sh.err("mkdir: " + str(e))


def touch(sh, args, line):
    if not args:
        return sh.err("usage: touch <file>")
    try:
        open(_r(args[0]), "a").close()
    except Exception as e:
        sh.err("touch: " + str(e))


def rm(sh, args, line):
    if not args:
        return sh.err("usage: rm [-r] <path>")
    recursive = "-r" in args or "-rf" in args
    targets = [a for a in args if not a.startswith("-")]
    for t in targets:
        try:
            p = _r(t)
            if os.path.isdir(p):
                if recursive:
                    shutil.rmtree(p)
                else:
                    sh.err("rm: " + t + ": is a directory (use -r)")
            else:
                os.remove(p)
        except Exception as e:
            sh.err("rm: " + str(e))


def cp(sh, args, line):
    if len(args) < 2:
        return sh.err("usage: cp <src> <dst>")
    try:
        shutil.copy(_r(args[0]), _r(args[1]))
    except Exception as e:
        sh.err("cp: " + str(e))


def mv(sh, args, line):
    if len(args) < 2:
        return sh.err("usage: mv <src> <dst>")
    try:
        shutil.move(_r(args[0]), _r(args[1]))
    except Exception as e:
        sh.err("mv: " + str(e))



COMMANDS = {
    "ls":     (ls,    "list directory contents",          "Files"),
    "cd":     (cd,    "change directory",                 "Files"),
    "pwd":    (pwd,   "print working directory",          "Files"),
    "cat":    (cat,   "print file contents",              "Files"),
    "mkdir":  (mkdir, "create a directory",               "Files"),
    "touch":  (touch, "create an empty file",             "Files"),
    "rm":     (rm,    "remove file or directory (-r)",    "Files"),
    "cp":     (cp,    "copy a file",                      "Files"),
    "mv":     (mv,    "move or rename a file",            "Files"),
}