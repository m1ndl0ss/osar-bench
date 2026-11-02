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
        self._emit("write", d, via="move")
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
                 "mv", "mkdir", "touch", "echo", "pwd", "cd", "sed", "curl", "stat", "test", "["}
    # flags that take a value, so the value is not mistaken for a path
    _VALUE_FLAGS = {
        "head": {"-n", "-c"}, "tail": {"-n", "-c"},
        "grep": {"-A", "-B", "-C", "-m"},
        "stat": {"-c", "--format"},
        "find": {"-name", "-iname", "-path", "-type", "-maxdepth", "-mindepth",
                 "-mtime", "-newer", "-size"},
    }

    def run_shell(self, command: str) -> str:
        outs = []
        for seg in re.split(r"\s*(?:&&|;)\s*", command.strip()):
            if seg:
                outs.append(self._pipeline(seg))
        return "\n".join(o for o in outs if o)

    def _pipeline(self, seg: str) -> str:
        stdin = None
        for part in [p.strip() for p in seg.split("|")]:
            stdin = self._cmd(part, stdin)
        return stdin or ""

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

    def _flag_value(self, args: list[str], flag: str) -> str | None:
        if flag in args and args.index(flag) + 1 < len(args):
            return args[args.index(flag) + 1]
        return None

    def _line_count(self, flags: list[str], args: list[str]) -> int:
        """head/tail: -n N, -nN or -N; default 10."""
        n = self._flag_value(args, "-n")
        for f in flags:
            if f[1:].isdigit():
                n = f[1:]
            elif f.startswith("-n") and f[2:].isdigit():
                n = f[2:]
        return int(n) if n and n.isdigit() else 10

    def _ls(self, arg: str, recursive: bool) -> str:
        """ls of one argument: a glob, a file or a directory."""
        if any(c in arg for c in "*?["):
            # the shell expands a glob by reading the parent directory
            self._emit("list", posixpath.dirname(self._abs(arg)))
            hits = [p for p in self._glob(arg) if p in self.files or p in self.dirs]
            return "\n".join(hits) if hits else f"ls: {arg}: no match"
        p = self._abs(arg)
        if p in self.files:
            self._emit("stat", p)
            return p
        if not recursive:
            return self.list_dir(p)
        self._emit("list", p, recursive=True)
        if not self._is_dir(p):
            return f"error: {p} is not a directory"
        base = p.rstrip("/")
        return "\n".join(sorted(q for q in set(self.files) | self.dirs if q.startswith(base + "/")))

    def _cmd(self, cmdline: str, stdin: str | None) -> str:
        # stderr redirects have no effect in the sandbox; drop them before parsing
        cmdline = re.sub(r"\s*(?:2>&1|[2&]>>?\S+)", "", cmdline)
        redirect, append = None, False
        m = re.search(r"\s(>>?)\s*(\S+)\s*$", " " + cmdline)
        if m:
            append = m.group(1) == ">>"
            redirect = m.group(2)
            cmdline = cmdline[: m.start(1) - 1].rstrip() if m.start(1) > 0 else ""
        try:
            argv = shlex.split(cmdline)
        except ValueError as e:
            return f"sh: parse error: {e}"
        if not argv:
            return ""
        cmd, args = argv[0], argv[1:]
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
            out = "\n".join(self._ls(g, rec) for g in (pos or ["."]))
        elif cmd in ("cat", "head", "tail", "wc", "stat"):
            if pos:
                texts = []
                for g in pos:
                    for t in self._glob(g):
                        texts.append(self.read_file(t) if cmd != "stat" else self._stat(t))
                text = "\n".join(texts)
            else:
                text = stdin or ""
            if cmd in ("head", "tail"):
                k = self._line_count(flags, args)
                lines = text.splitlines()
                text = "\n".join(lines[:k] if cmd == "head" else lines[-k:])
            elif cmd == "wc":
                text = f"{len(text.splitlines())} {len(text.split())} {len(text)}"
            out = text
        elif cmd == "grep":
            if not pos:
                return "grep: missing pattern"
            pat, targets = pos[0], pos[1:]
            rec = any("r" in f or "R" in f for f in flags)
            lines = []
            if targets:
                for g in targets:
                    for t in self._glob(g):
                        paths = ([f for f in self.files if f.startswith(t.rstrip('/') + '/')]
                                 if rec and self._is_dir(t) else [t])
                        for pth in sorted(paths):
                            txt = self.read_file(pth)
                            lines += [f"{pth}:{ln}" for ln in txt.splitlines() if re.search(pat, ln)]
            else:
                lines = [ln for ln in (stdin or "").splitlines() if re.search(pat, ln)]
            out = "\n".join(lines)
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
            out = " ".join(pos)
        elif cmd == "sed":
            inplace = any(f.startswith("-i") for f in flags)
            if len(pos) < 2:
                return "sed: usage: sed [-i] 's/a/b/' file"
            mm = re.match(r"s(.)(.*?)\1(.*?)\1(g?)$", pos[0])
            if not mm:
                return "sed: only s/// supported"
            res = []
            for t in self._glob(pos[1]):
                txt = self.read_file(t)
                new = re.sub(mm.group(2), mm.group(3), txt, count=0 if mm.group(4) else 1)
                if inplace:
                    res.append(self.write_file(t, new).replace("wrote", "edited"))
                else:
                    res.append(new)
            out = "\n".join(res)
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
            out = ""
        if redirect:
            if redirect != "/dev/null":
                self.write_file(redirect, out + "\n", append=append)
            return ""
        return out

    def _stat(self, p: str) -> str:
        self._emit("stat", p)
        if p in self.files:
            return f"{p}: file, {len(self.files[p])} bytes"
        if p in self.dirs:
            return f"{p}: directory"
        return f"stat: {p}: no such file"

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
        return out[:20000], [e.to_dict() for e in self.effects]
