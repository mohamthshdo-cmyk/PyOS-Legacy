"""PyShell parser - line to AST. Supports 2>&1, &>, &>>."""
class Token:
    WORD    = "WORD"
    PIPE    = "PIPE"
    AND     = "AND"
    OR      = "OR"
    SEMI    = "SEMI"
    GT      = "GT"
    GTGT    = "GTGT"
    LT      = "LT"
    ERRGT   = "ERRGT"
    ERRGTGT = "ERRGTGT"
    AMPGT   = "AMPGT"        # &>
    AMPGTGT = "AMPGTGT"      # &>>
    FD2TO1  = "FD2TO1"       # 2>&1
    def __init__(self, kind, value=""):
        self.kind = kind
        self.value = value

def _tokenize(line):
    tokens = []
    buf = []
    in_single = False
    in_double = False
    i = 0
    n = len(line)
    def flush():
        if buf:
            tokens.append(Token(Token.WORD, "".join(buf)))
            buf.clear()
    while i < n:
        c = line[i]
        if in_single:
            if c == "'":
                in_single = False; i += 1; continue
            buf.append(c); i += 1; continue
        if in_double:
            if c == '"':
                in_double = False; i += 1; continue
            if c == "\\" and i + 1 < n:
                buf.append(line[i + 1]); i += 2; continue
            buf.append(c); i += 1; continue
        if c == "\\" and i + 1 < n:
            buf.append(line[i + 1]); i += 2; continue
        if c == "'":
            in_single = True; i += 1; continue
        if c == '"':
            in_double = True; i += 1; continue

        # 2>&1
        _bound = (i == 0 or line[i-1].isspace() or line[i-1] in "|;&")
        if c == "2" and _bound and line[i:i+4] == "2>&1":
            flush(); tokens.append(Token(Token.FD2TO1)); i += 4; continue

        # &> and &>>
        if c == "&" and i + 1 < n and line[i + 1] == ">":
            flush()
            if i + 2 < n and line[i + 2] == ">":
                tokens.append(Token(Token.AMPGTGT)); i += 3
            else:
                tokens.append(Token(Token.AMPGT)); i += 2
            continue

        if c == "|":
            flush()
            if i + 1 < n and line[i + 1] == "|":
                tokens.append(Token(Token.OR)); i += 2
            else:
                tokens.append(Token(Token.PIPE)); i += 1
            continue
        if c == "&":
            flush()
            if i + 1 < n and line[i + 1] == "&":
                tokens.append(Token(Token.AND)); i += 2
            else:
                raise SyntaxError("unexpected '&' at position " + str(i))
            continue
        if c == ";":
            flush(); tokens.append(Token(Token.SEMI)); i += 1; continue
        if c == ">":
            flush()
            if i + 1 < n and line[i + 1] == ">":
                tokens.append(Token(Token.GTGT)); i += 2
            else:
                tokens.append(Token(Token.GT)); i += 1
            continue
        if c == "<":
            flush(); tokens.append(Token(Token.LT)); i += 1; continue
        if c == "2" and _bound and i + 1 < n and line[i + 1] == ">":
            flush()
            if i + 2 < n and line[i + 2] == ">":
                tokens.append(Token(Token.ERRGTGT)); i += 3
            else:
                tokens.append(Token(Token.ERRGT)); i += 2
            continue
        if c.isspace():
            flush(); i += 1; continue
        buf.append(c); i += 1
    if in_single or in_double:
        raise SyntaxError("unterminated quote")
    flush()
    return tokens

class Stage:
    def __init__(self):
        self.cmd = ""
        self.args = []
        self.redirects = {}
        # redirects keys:
        #   "stdout": (mode, filename)   mode in {write, append}
        #   "stderr": (mode, filename)
        #   "stdin":  ("read", filename)
        #   "merge_stderr_to_stdout": True   (from 2>&1)
        #   "both": (mode, filename)         (from &> or &>>)

class Pipeline:
    def __init__(self):
        self.stages = []

class ChainOp:
    def __init__(self, operator, pipeline):
        self.operator = operator
        self.pipeline = pipeline

def parse(line):
    line = line.strip()
    if not line:
        return []
    tokens = _tokenize(line)
    chain = []
    pipeline = Pipeline()
    stage = Stage()
    pending_op = None
    i = 0
    n = len(tokens)
    def close_stage():
        nonlocal stage
        if stage.cmd or stage.args or stage.redirects:
            pipeline.stages.append(stage)
        stage = Stage()
    def close_pipeline(next_op):
        nonlocal pipeline, pending_op
        close_stage()
        if pipeline.stages:
            chain.append(ChainOp(pending_op, pipeline))
        pipeline = Pipeline()
        pending_op = next_op
    while i < n:
        t = tokens[i]
        if t.kind in (Token.GT, Token.GTGT):
            if i + 1 >= n or tokens[i + 1].kind != Token.WORD:
                raise SyntaxError("redirect needs a filename")
            mode = "write" if t.kind == Token.GT else "append"
            stage.redirects["stdout"] = (mode, tokens[i + 1].value)
            i += 2; continue
        if t.kind in (Token.ERRGT, Token.ERRGTGT):
            if i + 1 >= n or tokens[i + 1].kind != Token.WORD:
                raise SyntaxError("redirect needs a filename")
            mode = "write" if t.kind == Token.ERRGT else "append"
            stage.redirects["stderr"] = (mode, tokens[i + 1].value)
            i += 2; continue
        if t.kind in (Token.AMPGT, Token.AMPGTGT):
            if i + 1 >= n or tokens[i + 1].kind != Token.WORD:
                raise SyntaxError("redirect needs a filename")
            mode = "write" if t.kind == Token.AMPGT else "append"
            stage.redirects["both"] = (mode, tokens[i + 1].value)
            i += 2; continue
        if t.kind == Token.FD2TO1:
            stage.redirects["merge_stderr_to_stdout"] = True
            i += 1; continue
        if t.kind == Token.LT:
            if i + 1 >= n or tokens[i + 1].kind != Token.WORD:
                raise SyntaxError("input redirect needs a filename")
            stage.redirects["stdin"] = ("read", tokens[i + 1].value)
            i += 2; continue
        if t.kind == Token.WORD:
            if not stage.cmd:
                stage.cmd = t.value
            else:
                stage.args.append(t.value)
            i += 1; continue
        if t.kind == Token.PIPE:
            close_stage(); i += 1; continue
        if t.kind in (Token.AND, Token.OR, Token.SEMI):
            op = {"AND": "&&", "OR": "||", "SEMI": ";"}[t.kind]
            close_pipeline(op)
            i += 1; continue
        raise SyntaxError("unexpected token")
    close_pipeline(None)
    return chain

def pretty(line):
    try:
        ast = parse(line)
    except SyntaxError as e:
        return "SyntaxError: " + str(e)
    out = []
    for op in ast:
        out.append("ChainOp(operator=" + repr(op.operator) + ")")
        for idx, st in enumerate(op.pipeline.stages):
            pre = "  +- " if idx == 0 else "  |  "
            out.append(pre + "Stage: cmd=" + repr(st.cmd) + " args=" + repr(st.args))
            if st.redirects:
                for k, v in st.redirects.items():
                    out.append(pre + "  redirect " + k + " " + repr(v))
    return "\n".join(out)
