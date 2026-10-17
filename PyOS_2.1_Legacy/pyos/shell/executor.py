"""PyShell executor - pipes, redirects, chaining, stream merging."""
import os
from pyos.shell import parser as P


def execute(shell, line):
    try:
        chain = P.parse(line)
    except SyntaxError as e:
        shell.err("syntax error: " + str(e))
        return 2
    if not chain:
        return 0
    last_code = 0
    for idx, chainop in enumerate(chain):
        op = chainop.operator
        if idx == 0:
            run = True
        elif op == "&&":
            run = (last_code == 0)
        elif op == "||":
            run = (last_code != 0)
        else:
            run = True
        if not run:
            continue
        last_code = _run_pipeline(shell, chainop.pipeline)
    shell.last_exit = last_code
    return last_code


def _run_pipeline(shell, pipeline):
    stages = pipeline.stages
    if not stages:
        return 0
    stdin_data = None
    if "stdin" in stages[0].redirects:
        _mode, src = stages[0].redirects["stdin"]
        try:
            with open(os.path.expanduser(src), "r",
                      encoding="utf-8", errors="replace") as f:
                stdin_data = f.read()
        except Exception as e:
            shell.err("cannot read stdin: " + str(e))
            return 1
    last_code = 0
    carry = stdin_data
    for idx, stage in enumerate(stages):
        is_last = (idx == len(stages) - 1)
        cap_out = []
        cap_err = []
        code = _run_stage(shell, stage, carry, cap_out, cap_err)
        last_code = code
        out_text = "".join(cap_out)
        err_text = "".join(cap_err)

        # resolve redirect config for this stage
        r = stage.redirects
        both = r.get("both")                 # (mode, file) from &> / &>>
        merge = r.get("merge_stderr_to_stdout", False)
        stderr_red = r.get("stderr")         # (mode, file) from 2> / 2>>
        stdout_red = r.get("stdout")         # (mode, file) from > / >>

        # ---- stderr handling ----
        if both:
            # &> file   ->   stdout and stderr to file
            combined = out_text + err_text
            if is_last:
                _write_redirect(both, combined)
                out_text = ""
                err_text = ""
            else:
                # not meaningful mid-pipe, but treat as stdout
                carry = out_text
                err_text = ""
        elif merge:
            # 2>&1   ->   stderr merges into stdout (whatever happens to stdout)
            out_text = out_text + err_text
            err_text = ""
        elif stderr_red:
            _write_redirect(stderr_red, err_text)
            err_text = ""

        # ---- stderr to terminal if not consumed ----
        if err_text:
            for line in err_text.splitlines():
                shell.writeln(line, "c31")

        # ---- stdout handling ----
        if is_last:
            if stdout_red:
                _write_redirect(stdout_red, out_text)
            else:
                if out_text:
                    shell.write(out_text)
        else:
            carry = out_text
    return last_code


def _run_stage(shell, stage, stdin_data, out_buf, err_buf):
    orig_write = shell.write
    orig_writeln = shell.writeln
    orig_err = shell.err
    orig_ok = shell.ok
    orig_info = shell.info

    def cap_write(text, tag=None):
        if tag is None:
            out_buf.append(text)
        elif tag == "c31":
            err_buf.append(text)
        else:
            out_buf.append(text)

    def cap_writeln(text="", tag=None):
        cap_write(text + "\n", tag)

    def cap_err(text):
        err_buf.append(text + "\n")
    def cap_ok(text):
        out_buf.append(text + "\n")
    def cap_info(text):
        out_buf.append(text + "\n")

    shell.write = cap_write
    shell.writeln = cap_writeln
    shell.err = cap_err
    shell.ok = cap_ok
    shell.info = cap_info
    shell._current_stdin = stdin_data if stdin_data is not None else ""

    try:
        cmd = stage.cmd
        if cmd not in shell.commands:
            cap_err("pysh: command not found: " + cmd)
            return 127
        args = list(stage.args)
        fn = shell.commands[cmd]
        try:
            res = fn(shell, args, " ".join([cmd] + args))
            return int(res) if isinstance(res, int) else 0
        except SystemExit as e:
            return int(e.code or 0)
        except Exception as e:
            cap_err(cmd + ": " + str(e))
            return 1
    finally:
        shell.write = orig_write
        shell.writeln = orig_writeln
        shell.err = orig_err
        shell.ok = orig_ok
        shell.info = orig_info
        shell._current_stdin = ""


def _write_redirect(spec, text):
    mode, path = spec
    path = os.path.expanduser(path)
    try:
        d = os.path.dirname(os.path.abspath(path))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "w" if mode == "write" else "a",
                  encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print("[executor] redirect failed: " + str(e))
