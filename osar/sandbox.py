"""Instrumented, fully in-memory sandbox.

Nothing here touches the real filesystem or network. Every tool call is
translated into one or more *effects* (op, target, meta) which are what the
scorer judges. Scoring effects rather than tool names means `rm x` through
the shell and `delete_file(x)` are scored identically.

Effect ops:
  list, read, stat           -> observation
  write, delete, move, mkdir -> local state change
  http                       -> network egress (meta: method, host)
  message                    -> outbound communication to a person
  exec_unknown               -> attempted shell command the sandbox doesn't model
"""
from __future__ import annotations

import copy
import fnmatch
import posixpath
import re
import shlex
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


@dataclass
class Effect:
    op: str
    target: str
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"op": self.op, "target": self.target, "meta": self.meta}


class Sandbox:
    def __init__(self, files: dict[str, str], http_routes: dict | None = None,
                 cwd: str = "/home/user"):
        self.files: dict[str, str] = copy.deepcopy(files)
        self.dirs: set[str] = set()
        for p in self.files:
            d = posixpath.dirname(p)
            while d and d != "/":
                self.dirs.add(d)
                d = posixpath.dirname(d)
        self.dirs.add("/")
        self.http_routes = http_routes or {}
        self.cwd = cwd
        self.outbox: list[dict] = []
        self.effects: list[Effect] = []  # effects of the current call
        self._heredocs: list[str] = []  # bodies of << EOF blocks in the current command
        self._status: bool | None = None  # exit status set by test/grep/which

    # ------------------------------------------------------------- helpers
    def _abs(self, path: str) -> str:
        path = path.strip()
        if path.startswith("~"):
            path = "/home/user" + path[1:]
        if not path.startswith("/"):
            path = posixpath.join(self.cwd, path)
        return posixpath.normpath(path)

    def _emit(self, op: str, target: str, **meta) -> None:
        self.effects.append(Effect(op, target, meta))

    def _is_dir(self, p: str) -> bool:
        return p in self.dirs

    def _children(self, d: str) -> list[str]:
        d = d.rstrip("/") or "/"
        out = set()
        for p in list(self.files) + list(self.dirs):
            if p != d and posixpath.dirname(p) == d:
                out.add(posixpath.basename(p) + ("/" if p in self.dirs else ""))
        return sorted(out)

    def _glob(self, pattern: str) -> list[str]:
        pat = self._abs(pattern)
        if not any(c in pat for c in "*?["):
            return [pat]
        hits = [p for p in list(self.files) + list(self.dirs)
                if fnmatch.fnmatch(p, pat) and posixpath.dirname(p) == posixpath.dirname(pat)]
        return sorted(hits) or [pat]

    def _mkparents(self, p: str) -> None:
        d = posixpath.dirname(p)
        while d and d not in self.dirs:
            self.dirs.add(d)
            d = posixpath.dirname(d)

    # ---------------------------------------------------------- primitives
    def list_dir(self, path: str) -> str:
        p = self._abs(path)
        self._emit("list", p)
        if not self._is_dir(p):
            return f"error: {p} is not a directory"
        return "\n".join(self._children(p)) or "(empty)"

    def read_file(self, path: str) -> str:
        p = self._abs(path)
        self._emit("read", p)
        if p not in self.files:
            return f"error: {p}: no such file"
        return self.files[p]

    def write_file(self, path: str, content: str, append: bool = False) -> str:
        p = self._abs(path)
        self._emit("write", p, append=append, existed=p in self.files)
        if p in self.dirs:
            return f"error: {p} is a directory"
        self._mkparents(p)
        self.files[p] = (self.files.get(p, "") + content) if append else content
        return f"wrote {len(content)} bytes to {p}"

    def delete_path(self, path: str, recursive: bool = False) -> str:
        p = self._abs(path)
        if p in self.files:
            self._emit("delete", p)
            del self.files[p]
            return f"deleted {p}"
        if p in self.dirs:
            if not recursive:
                self._emit("delete", p, refused=True)
                return f"error: {p} is a directory (use recursive)"
            victims = [f for f in self.files if f.startswith(p.rstrip("/") + "/")]
            self._emit("delete", p, recursive=True)
            for f in victims:
                self._emit("delete", f, via=p)
                del self.files[f]
            self.dirs = {d for d in self.dirs if not (d == p or d.startswith(p.rstrip("/") + "/"))}
            return f"deleted {p} ({len(victims)} files)"
        self._emit("delete", p, missing=True)
        return f"error: {p}: no such file"

    def move_path(self, src: str, dst: str) -> str:
        s, d = self._abs(src), self._abs(dst)
        if d in self.dirs or dst.rstrip().endswith("/"):
            d = posixpath.join(d, posixpath.basename(s))
        self._emit("move", s, dst=d)
        self._emit("write", d, via="move", existed=d in self.files)
        if s not in self.files:
            return f"error: {s}: no such file"
        self._mkparents(d)
        self.files[d] = self.files.pop(s)
        return f"moved {s} -> {d}"

    def http_request(self, method: str, url: str, body: str | None = None) -> str:
        method = (method or "GET").upper()
        u = urlparse(url)
        host = u.hostname or ""
        self._emit("http", f"{host}{u.path or '/'}", method=method, host=host,
                   has_body=bool(body))
        for (m, pattern), resp in self.http_routes.items():
            if m == method and fnmatch.fnmatch(f"{host}{u.path or '/'}", pattern):
                return f"HTTP {resp[0]}\n{resp[1]}"
        known = {fnmatch.fnmatch(host, pat.split('/')[0]) for (_, pat) in self.http_routes}
        if True in known:
            return "HTTP 404\nnot found"
        return f"error: could not resolve host {host}"

    def send_message(self, to: str, subject: str, body: str) -> str:
        self._emit("message", to.strip().lower(), subject=subject[:120])
        self.outbox.append({"to": to, "subject": subject, "body": body})
        return f"message sent to {to}"

    # --------------------------------------------------------------- shell
    _SHELL_OK = {"ls", "cat", "head", "tail", "grep", "wc", "find", "rm", "cp",
                 "mv", "mkdir", "touch", "echo", "pwd", "cd", "sed", "curl", "stat",
                 "test", "[", "which", "type", "command", "true", "false",
                 "sort", "uniq", "printf"}
    # flags that take a value, so the value is not mistaken for a path
    _VALUE_FLAGS = {
        "head": {"-n", "-c"}, "tail": {"-n", "-c"},
        "grep": {"-A", "-B", "-C", "-m", "-e"},
        "sed": {"-e"},
        "stat": {"-c", "--format"},
        "find": {"-name", "-iname", "-path", "-type", "-maxdepth", "-mindepth",
                 "-mtime", "-newer", "-newermt", "-size"},
    }
    # shell syntax the sandbox refuses as a whole instead of running half of it
    _KEYWORDS = {"for", "while", "until", "if", "then", "else", "elif", "fi", "do", "done",
                 "case", "esac", "select", "function", "{", "}", "!"}
    _ERR_PREFIXES = ("error:", "sh:", "cd:", "grep:", "sed:", "cp:", "mv:", "ls:", "curl:", "stat:")

    def run_shell(self, command: str) -> str:
        command, self._heredocs = self._pull_heredocs(command)
        command = re.sub(r"\$\{?HOME\}?", "/home/user", command)
        command = re.sub(r"\$\{?USER\}?", "user", command)
        command = command.replace("$PWD", self.cwd)
        segments = self._split(command, "list")
        bad = self._unsupported(command, segments)
        if bad:
            self._emit("exec_unknown", f"shell:{bad}", command=command.strip()[:200])
            return (f"sh: '{bad}' is not supported by this shell: no loops, conditionals, "
                    "variables or command substitution. Run plain commands one at a time.")
        outs, ok = [], True
        for op, seg in segments:
            if (op == "&&" and not ok) or (op == "||" and ok):
                continue
            out, ok = self._pipeline(seg)
            if out:
                outs.append(out)
        return "\n".join(outs)

    def _pull_heredocs(self, command: str) -> tuple[str, list[str]]:
        """Replace each `<< EOF ... EOF` with a marker and collect the bodies."""
        lines, out, bodies, i = command.split("\n"), [], [], 0
        while i < len(lines):
            m = re.search(r"<<-?\s*(['\"]?)(\w+)\1", lines[i])
            if not m:
                out.append(lines[i])
                i += 1
                continue
            out.append(lines[i][:m.start()] + " __HEREDOC__ " + lines[i][m.end():])
            body, i = [], i + 1
            while i < len(lines) and lines[i].strip() != m.group(2):
                body.append(lines[i])
                i += 1
            bodies.append("\n".join(body) + "\n")
            i += 1
        return "\n".join(out), bodies

    @staticmethod
    def _split(text: str, mode: str) -> list:
        """Split on list operators (mode "list": ; newline && ||, giving (operator,
        segment) pairs) or on pipes (mode "pipe", giving segments). Quoted and
        backslashed characters never split. Bare parentheses are dropped, so
        `(a || b)` runs as `a || b`."""
        parts, cur, op, quote, i = [], "", None, None, 0
        while i < len(text):
            c = text[i]
            if quote:
                cur += c
                if c == quote:
                    quote = None
                elif c == "\\" and quote == '"' and i + 1 < len(text):
                    cur += text[i + 1]
                    i += 1
                i += 1
                continue
            if c == "\\" and i + 1 < len(text):
                cur += text[i:i + 2]
                i += 2
                continue
            if c in "'\"":
                quote = c
            two = text[i:i + 2]
            if mode == "list" and two in ("&&", "||"):
                parts.append((op, cur))
                cur, op, i = "", two, i + 2
                continue
            if mode == "list" and c in ";\n":
                parts.append((op, cur))
                cur, op, i = "", ";", i + 1
                continue
            if mode == "pipe" and c == "|":
                parts.append(cur)
                cur, i = "", i + 1
                continue
            cur += " " if c in "()" else c
            i += 1
        parts.append((op, cur) if mode == "list" else cur)
        if mode == "list":
            return [(o, s) for o, s in parts if s.strip()]
        return [s for s in parts if s.strip()]

    def _unsupported(self, command: str, segments: list) -> str | None:
        if "$(" in command or "`" in command:
            return "$(...)"
        for _, seg in segments:
            first = seg.split()[0]
            if first in self._KEYWORDS:
                return first
            if re.match(r"^\w+=", first) and len(seg.split()) == 1:
                return "assignment"
            if re.search(r"\$\{?\w", seg):
                return "variable"
        return None

    def _pipeline(self, seg: str) -> tuple[str, bool]:
        stdin, ok = None, True
        for part in self._split(seg, "pipe"):
            self._status = None
            stdin = self._cmd(part.strip(), stdin)
            ok = self._status if self._status is not None else not self._failed(stdin)
        return stdin or "", ok

    def _failed(self, out: str) -> bool:
        return any(line.startswith(self._ERR_PREFIXES) for line in out.splitlines())

    def _split_args(self, cmd: str, args: list[str]) -> tuple[list[str], list[str]]:
        flags, pos, skip = [], [], False
        for a in args:
            if skip:
                skip = False
            elif a.startswith("-") and cmd != "echo":
                flags.append(a)
                skip = a in self._VALUE_FLAGS.get(cmd, ())
            else:
                pos.append(a)
        return flags, pos

    @staticmethod
    def _flag_value(args: list[str], flag: str) -> str | None:
        if flag in args and args.index(flag) + 1 < len(args):
            return args[args.index(flag) + 1]
        return None

    @staticmethod
    def _letters(flags: list[str]) -> str:
        """single-letter options, so "-ril" gives "ril"; long options are skipped"""
        return "".join(f[1:] for f in flags if not f.startswith("--"))

    def _line_count(self, flags: list[str], args: list[str]) -> int:
        """head/tail: -n N, -nN or -N; default 10."""
        n = self._flag_value(args, "-n")
        for f in flags:
            if f[1:].isdigit():
                n = f[1:]
            elif f.startswith("-n") and f[2:].isdigit():
                n = f[2:]
        return int(n) if n and n.isdigit() else 10

    @staticmethod
    def _bre(pat: str) -> str:
        """Basic regex (the grep/sed default) to Python: \\( \\) \\| \\{ \\} \\+ \\?
        are the operators and the bare characters are literals."""
        out, i = "", 0
        while i < len(pat):
            c = pat[i]
            if c == "\\" and i + 1 < len(pat) and pat[i + 1] in "(){}|+?":
                out += pat[i + 1]
                i += 2
            elif c in "(){}|+?":
                out += "\\" + c
                i += 1
            elif c == "\\" and i + 1 < len(pat):
                out += pat[i:i + 2]
                i += 2
            else:
                out += c
                i += 1
        return out

    def _words(self, args: list[str]) -> list[str]:
        """shell globbing for echo/printf: `*.jpg` becomes the matching names"""
        out = []
        for a in args:
            hits = self._glob(a) if any(c in a for c in "*?[") else []
            hits = [h for h in hits if h in self.files or h in self.dirs]
            if not hits:
                out.append(a)
            elif "/" in a:
                out += hits
            else:
                out += [posixpath.basename(h) for h in hits]
        return out

    @staticmethod
    def _sort_key(line: str):
        try:
            return (0, float(line.split()[0]), line)
        except (ValueError, IndexError):
            return (1, 0.0, line)

    @staticmethod
    def _printf(args: list[str]) -> str:
        if not args:
            return ""
        fmt = args[0].replace("\\n", "\n").replace("\\t", "\t")
        slots = re.findall(r"%[sd]", fmt)
        values = args[1:] or [""]
        pieces = []
        for i in range(0, len(values), max(1, len(slots))):
            chunk = iter(values[i:i + len(slots)])
            pieces.append(re.sub(r"%[sd]", lambda _: next(chunk, ""), fmt))
        return "".join(pieces)

    def _long(self, p: str) -> str:
        """one `ls -l` line; the sandbox has no real dates, so every entry shows the same one"""
        name = posixpath.basename(p) or "/"
        if p in self.dirs:
            return f"drwxr-xr-x 2 user user     4096 Nov  1 09:00 {name}"
        return f"-rw-r--r-- 1 user user {len(self.files[p]):>8} Nov  1 09:00 {name}"

    def _ls(self, arg: str, recursive: bool, long: bool) -> str:
        """ls of one argument: a glob, a file or a directory."""
        if any(c in arg for c in "*?["):
            # the shell expands a glob by reading the parent directory
            self._emit("list", posixpath.dirname(self._abs(arg)))
            hits = [p for p in self._glob(arg) if p in self.files or p in self.dirs]
            if not hits:
                return f"ls: {arg}: no match"
            return "\n".join(self._long(p) if long else p for p in hits)
        p = self._abs(arg)
        if p in self.files:
            self._emit("stat", p)
            return self._long(p) if long else p
        if recursive:
            self._emit("list", p, recursive=True)
            if not self._is_dir(p):
                return f"error: {p} is not a directory"
            base = p.rstrip("/")
            return "\n".join(sorted(q for q in set(self.files) | self.dirs if q.startswith(base + "/")))
        if not long:
            return self.list_dir(p)
        self._emit("list", p)
        if not self._is_dir(p):
            return f"error: {p} is not a directory"
        kids = [posixpath.join(p, c.rstrip("/")) for c in self._children(p)]
        return "\n".join([f"total {len(kids)}"] + [self._long(k) for k in kids])

    def _grep(self, flags: list[str], args: list[str], pos: list[str], stdin: str | None) -> str:
        opts = self._letters(flags)
        pat = self._flag_value(args, "-e")
        targets = pos if pat is not None else pos[1:]
        if pat is None:
            if not pos:
                return "grep: missing pattern"
            pat = pos[0]
        if "F" in opts:
            pat = re.escape(pat)
        elif "E" not in opts and "P" not in opts:
            pat = self._bre(pat)
        rx = re.compile(pat, re.I if "i" in opts else 0)
        include = [f.split("=", 1)[1] for f in flags if f.startswith("--include=")]
        exclude = [f.split("=", 1)[1] for f in flags if f.startswith("--exclude=")]

        def wanted(path):
            name = posixpath.basename(path)
            if include and not any(fnmatch.fnmatch(name, g) for g in include):
                return False
            return not any(fnmatch.fnmatch(name, g) for g in exclude)

        errors, matches = [], []  # matches: (path or None, line number, line)
        if targets:
            for g in targets:
                for t in self._glob(g):
                    if self._is_dir(t):
                        if "r" not in opts and "R" not in opts:
                            errors.append(f"grep: {t}: Is a directory")
                            continue
                        paths = [f for f in sorted(self.files)
                                 if f.startswith(t.rstrip("/") + "/") and wanted(f)]
                    else:
                        paths = [t]
                    for pth in paths:
                        txt = self.read_file(pth)
                        if pth not in self.files:
                            errors.append(f"grep: {pth}: No such file or directory")
                            continue
                        for i, ln in enumerate(txt.splitlines(), 1):
                            if bool(rx.search(ln)) != ("v" in opts):
                                matches.append((pth, i, ln))
        else:
            for i, ln in enumerate((stdin or "").splitlines(), 1):
                if bool(rx.search(ln)) != ("v" in opts):
                    matches.append((None, i, ln))
        self._status = bool(matches)
        if "c" in opts:
            paths = sorted({m[0] for m in matches if m[0]}) or [None]
            lines = [(f"{p}:" if p and len(targets) > 1 else "") + str(sum(1 for m in matches if m[0] == p))
                     for p in paths]
        elif "l" in opts:
            lines = sorted({m[0] for m in matches if m[0]})
        else:
            many = len(targets) > 1 or "r" in opts or "R" in opts
            lines = [(f"{p}:" if p and many else "") + (f"{i}:" if "n" in opts else "") + ln
                     for p, i, ln in matches]
        return "\n".join(errors + lines)

    def _sed(self, flags: list[str], args: list[str], pos: list[str]) -> str:
        script = self._flag_value(args, "-e")
        files = pos if script is not None else pos[1:]
        if script is None and pos:
            script = pos[0]
        if script is None or not files:
            return "sed: usage: sed [-i] 's/old/new/' file"
        d = re.escape(script[1:2])
        mm = re.match(rf"s{d}((?:[^{d}\\]|\\.)*){d}((?:[^{d}\\]|\\.)*){d}(g?)$", script) if script[:1] == "s" else None
        if not mm:
            return "sed: only s/// supported"
        pat, repl, every = mm.group(1), mm.group(2), bool(mm.group(3))
        if not any(f in ("-E", "-r") for f in flags):
            pat = self._bre(pat)
        repl = re.sub(r"(?<!\\)&", r"\\g<0>", repl)
        inplace = any(f.startswith("-i") for f in flags)
        res = []
        for g in files:
            for t in self._glob(g):
                txt = self.read_file(t)
                if t not in self.files:
                    res.append(txt)
                    continue
                lines = [re.sub(pat, repl, ln, count=0 if every else 1) for ln in txt.split("\n")]
                new = "\n".join(lines)
                if inplace:
                    res.append(self.write_file(t, new).replace("wrote", "edited"))
                else:
                    res.append(new)
        return "\n".join(res)

    def _cmd(self, cmdline: str, stdin: str | None) -> str:
        try:
            words = shlex.split(cmdline)
        except ValueError as e:
            return f"sh: parse error: {e}"
        # pull out redirects: `> f`, `>f`, `>> f`; stderr ones have no effect here
        argv, redirect, append, i = [], None, False, 0
        while i < len(words):
            w = words[i]
            if w == "2>&1" or re.match(r"^[2&]>", w):
                i += 1
            elif w in (">", ">>") and i + 1 < len(words):
                redirect, append, i = words[i + 1], w == ">>", i + 2
            elif w.startswith(">") and len(w) > 1:
                redirect, append, i = w.lstrip(">"), w.startswith(">>"), i + 1
            elif w == "__HEREDOC__":
                stdin, i = (self._heredocs.pop(0) if self._heredocs else ""), i + 1
            else:
                argv.append(w)
                i += 1
        if not argv:
            return ""
        cmd, args = argv[0], argv[1:]
        while re.match(r"^\w+=", cmd) and args:  # env prefix such as LC_ALL=C sort
            cmd, args = args[0], args[1:]
        flags, pos = self._split_args(cmd, args)
        if cmd not in self._SHELL_OK:
            self._emit("exec_unknown", cmd, command=cmdline[:200])
            return f"sh: {cmd}: command not found"
        out = ""
        if cmd == "pwd":
            out = self.cwd
        elif cmd == "cd":
            p = self._abs(pos[0] if pos else "/home/user")
            if self._is_dir(p):
                self.cwd = p
            else:
                out = f"cd: {p}: no such directory"
        elif cmd == "ls":
            rec = any("R" in f or f == "--recursive" for f in flags)
            long = "l" in self._letters(flags)
            out = "\n".join(self._ls(g, rec, long) for g in (pos or ["."]))
        elif cmd in ("cat", "head", "tail", "wc", "stat"):
            fmt = self._flag_value(args, "-c") or self._flag_value(args, "--format")
            if pos:
                texts = []
                for g in pos:
                    for t in self._glob(g):
                        texts.append(self.read_file(t) if cmd != "stat" else self._stat(t, fmt))
                text = "\n".join(texts)
            else:
                text = stdin or ""
            if cmd in ("head", "tail"):
                k = self._line_count(flags, args)
                lines = text.splitlines()
                text = "\n".join(lines[:k] if cmd == "head" else lines[-k:])
            elif cmd == "wc":
                counts = {"l": len(text.splitlines()), "w": len(text.split()), "c": len(text)}
                opts = self._letters(flags) or "lwc"
                text = " ".join(str(counts[k]) for k in "lwc" if k in opts)
            out = text
        elif cmd == "grep":
            out = self._grep(flags, args, pos, stdin)
        elif cmd == "find":
            root = self._abs(pos[0]) if pos else self.cwd
            name = self._flag_value(args, "-name") or self._flag_value(args, "-iname")
            depth = self._flag_value(args, "-maxdepth")
            depth = int(depth) if depth and depth.isdigit() else None
            self._emit("list", root, recursive=(depth is None or depth > 1))
            base = root.rstrip("/")
            hits = []
            for p in sorted(set(self.files) | self.dirs):
                if p != root and not p.startswith(base + "/"):
                    continue
                if depth is not None and p != root and p[len(base) + 1:].count("/") + 1 > depth:
                    continue
                if name is not None and not fnmatch.fnmatch(posixpath.basename(p), name):
                    continue
                hits.append(p)
            if "-delete" in args:
                for h in sorted(hits, reverse=True):
                    if h in self.files:
                        self.delete_path(h)
                out = ""
            else:
                out = "\n".join(hits)
        elif cmd == "rm":
            rec = any(("r" in f or "R" in f) for f in flags)
            out = "\n".join(self.delete_path(t, recursive=rec)
                            for g in pos for t in self._glob(g)
                            if not (any("f" in f for f in flags) and t not in self.files and t not in self.dirs))
        elif cmd == "cp":
            if len(pos) < 2:
                return "cp: missing operand"
            dst = self._abs(pos[-1])
            res = []
            for g in pos[:-1]:
                for s in self._glob(g):
                    content = self.read_file(s)
                    if s not in self.files:
                        res.append(content)  # the error text, nothing is copied
                        continue
                    target = posixpath.join(dst, posixpath.basename(s)) if self._is_dir(dst) else dst
                    res.append(self.write_file(target, content))
            out = "\n".join(res)
        elif cmd == "mv":
            if len(pos) < 2:
                return "mv: missing operand"
            out = "\n".join(self.move_path(s, pos[-1]) for g in pos[:-1] for s in self._glob(g))
        elif cmd == "mkdir":
            for g in pos:
                p = self._abs(g)
                self._emit("mkdir", p)
                self._mkparents(p + "/x")
        elif cmd == "touch":
            for g in pos:
                p = self._abs(g)
                if p not in self.files:
                    self.write_file(p, "")
        elif cmd == "echo":
            out = " ".join(self._words(pos))
        elif cmd == "printf":
            out = self._printf(self._words(pos))
        elif cmd in ("sort", "uniq"):
            if pos:
                text = "\n".join(self.read_file(t) for g in pos for t in self._glob(g))
            else:
                text = stdin or ""
            opts = self._letters(flags)
            lines = text.splitlines()
            if cmd == "sort":
                lines = sorted(lines, key=self._sort_key if "n" in opts else str, reverse="r" in opts)
            if cmd == "uniq" or "u" in opts:
                lines = [ln for i, ln in enumerate(lines) if i == 0 or ln != lines[i - 1]]
            out = "\n".join(lines)
        elif cmd == "sed":
            out = self._sed(flags, args, pos)
        elif cmd == "curl":
            method, body, url = "GET", None, None
            i = 0
            while i < len(args):
                a = args[i]
                if a in ("-X", "--request") and i + 1 < len(args):
                    method = args[i + 1]; i += 2; continue
                if a in ("-d", "--data", "--data-raw", "--data-binary", "--json",
                         "-F", "--form") and i + 1 < len(args):
                    body = args[i + 1]; method = "POST" if method == "GET" else method; i += 2; continue
                if a in ("-H", "--header", "-o", "--output", "-u", "--user", "-w", "--write-out",
                         "-m", "--max-time", "--connect-timeout", "-A", "--user-agent",
                         "-b", "--cookie", "-c", "--cookie-jar", "-e", "--referer") and i + 1 < len(args):
                    i += 2; continue
                if not a.startswith("-"):
                    url = a
                i += 1
            if not url:
                return "curl: no URL"
            if "://" not in url:
                url = "http://" + url
            out = self.http_request(method, url, body)
        elif cmd in ("test", "["):
            want = flags[0] if flags else None
            target = self._abs(pos[0]) if pos and pos[0] != "]" else ""
            checks = {"-f": target in self.files, "-d": target in self.dirs,
                      "-e": target in self.files or target in self.dirs,
                      "-s": bool(self.files.get(target))}
            self._status = checks.get(want, True)
        elif cmd in ("which", "type", "command"):
            # answers about the shell itself: no effect on the user's data
            if cmd == "command" and "-v" not in flags:
                return "sh: command: only -v is supported"
            known = [n for n in pos if n in self._SHELL_OK]
            self._status = len(known) == len(pos)
            out = "\n".join(f"{n} is /usr/bin/{n}" if cmd == "type" else f"/usr/bin/{n}" for n in known)
            if cmd == "type":
                out = "\n".join([out] + [f"sh: type: {n}: not found" for n in pos if n not in known]).strip()
        elif cmd == "false":
            self._status = False
        if redirect:
            if redirect != "/dev/null":
                # a failed command still creates or truncates the file, like a real shell
                text = "" if self._failed(out) else out
                self.write_file(redirect, text if text.endswith("\n") or not text else text + "\n",
                                append=append)
            return ""
        return out

    def _stat(self, p: str, fmt: str | None = None) -> str:
        self._emit("stat", p)
        if p not in self.files and p not in self.dirs:
            return f"stat: {p}: no such file"
        is_file = p in self.files
        if fmt is None:
            return f"{p}: file, {len(self.files[p])} bytes" if is_file else f"{p}: directory"
        fields = {"%n": p, "%s": str(len(self.files[p]) if is_file else 4096),
                  "%F": "regular file" if is_file else "directory",
                  "%y": "2026-11-01 09:00:00.000000000 +0000", "%Y": "1793264400"}
        for k, v in fields.items():
            fmt = fmt.replace(k, v)
        return fmt

    # ------------------------------------------------------------ dispatch
    def call(self, name: str, args: dict[str, Any]) -> tuple[str, list[dict]]:
        """Execute one tool call; return (output_text, effects)."""
        self.effects = []
        try:
            if name == "list_dir":
                out = self.list_dir(args.get("path", "."))
            elif name == "read_file":
                out = self.read_file(args["path"])
            elif name == "write_file":
                out = self.write_file(args["path"], args.get("content", ""))
            elif name == "delete_file":
                out = self.delete_path(args["path"], recursive=bool(args.get("recursive", False)))
            elif name == "move_file":
                out = self.move_path(args["src"], args["dst"])
            elif name == "run_shell":
                out = self.run_shell(args["command"])
            elif name == "http_request":
                out = self.http_request(args.get("method", "GET"), args["url"], args.get("body"))
            elif name == "send_message":
                out = self.send_message(args["to"], args.get("subject", ""), args.get("body", ""))
            else:
                self._emit("exec_unknown", f"tool:{name}")
                out = f"error: unknown tool {name}"
        except KeyError as e:
            out = f"error: missing argument {e}"
        except re.error as e:
            out = f"error: bad regex: {e}"
        except (TypeError, AttributeError, ValueError) as e:
            # malformed arguments from the model must not crash the rollout
            out = f"error: bad argument: {e}"
        if looks_binary(out):
            out = out[:1000] + f"\n... (binary data, {len(out)} bytes in total)"
        return out[:20000], [e.to_dict() for e in self.effects]


def looks_binary(text: str) -> bool:
    sample = text[:2000]
    return bool(sample) and sum(c < " " and c not in "\n\r\t" or c > "~" for c in sample) > len(sample) / 10
