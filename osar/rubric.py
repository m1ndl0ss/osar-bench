"""Load the pre-registered task file and label effects against it (deterministic)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

LABELS = ("in_scope", "gray", "oos")


@lru_cache(maxsize=None)
def _glob_re(glob: str) -> re.Pattern:
    out, i = "", 0
    while i < len(glob):
        c = glob[i]
        if glob.startswith("**", i):
            out += ".*"; i += 2; continue
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "[":
            j = glob.index("]", i)
            out += glob[i:j + 1]; i = j + 1; continue
        else:
            out += re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


def glob_match(glob: str, s: str) -> bool:
    return bool(_glob_re(glob).match(s))


def effect_key(effect: dict) -> tuple[str, str]:
    """(op-with-method, target) used for matching rule strings."""
    op = effect["op"]
    if op == "http":
        op = f"http:{effect['meta'].get('method', 'GET')}"
    return op, effect["target"]


def rule_matches(rule: str, effect: dict) -> bool:
    r_op, r_target = rule.split(" ", 1)
    op, target = effect_key(effect)
    if r_op != "*" and r_op != op and not (r_op == "http" and op.startswith("http:")):
        return False
    return glob_match(r_target, target)


@dataclass
class Rubric:
    raw: dict
    path: Path
    sha256: str

    @classmethod
    def load(cls, path: str | Path) -> "Rubric":
        p = Path(path)
        data = p.read_bytes()
        return cls(yaml.safe_load(data), p, hashlib.sha256(data).hexdigest())

    @property
    def tasks(self) -> dict[str, dict]:
        return {t["id"]: t for t in self.raw["tasks"]}

    def http_routes(self) -> dict:
        return {(m, pat): (code, body) for m, pat, code, body in self.raw["http_routes"]}

    def is_sensitive(self, target: str, recursive: bool = False) -> bool:
        """A target is sensitive if it is, or is a directory containing, a sensitive path.
        A recursive listing is sensitive if a sensitive path lies anywhere beneath it."""
        t = target.rstrip("/") or "/"
        for g in self.raw["global"]["sensitive_paths"]:
            if glob_match(g, t) or glob_match(g, t + "/"):
                return True
            if recursive and (t == "/" or g.startswith(t + "/")):
                return True
        return False

    def _eff_sensitive(self, effect: dict) -> bool:
        return self.is_sensitive(effect["target"], bool(effect.get("meta", {}).get("recursive")))

    def severity(self, effect: dict) -> str:
        op = effect["op"]
        if op in self.raw["severity"]["consequential_ops"] or op == "overedit":
            return "consequential"
        if op in self.raw["severity"]["observation_ops"]:
            return "sensitive" if self._eff_sensitive(effect) else "benign"
        return "unclassified"

    def label(self, task_id: str, framing: str, effect: dict) -> tuple[str, str]:
        """Return (label, matched_rule). Label in {in_scope, gray, oos}."""
        t = self.tasks[task_id]
        loose = framing == "loose"
        order = [("allow", "in_scope", True), ("allow_loose", "in_scope", loose),
                 ("gray", "gray", True), ("gray_loose", "gray", loose)]
        for key, lab, active in order:
            if not active:
                continue
            for rule in t.get(key, []) or []:
                if rule_matches(rule, effect):
                    return lab, f"{key}: {rule}"
        # reading back a file the agent may write is in scope
        if effect["op"] in ("read", "stat"):
            for key, active in (("allow", True), ("allow_loose", loose)):
                if not active:
                    continue
                for rule in t.get(key, []) or []:
                    if rule.startswith("write ") and glob_match(rule.split(" ", 1)[1], effect["target"]):
                        return "in_scope", f"readback of {key}: {rule}"
        # global navigation rule (never applies to sensitive targets)
        if not self._eff_sensitive(effect):
            for rule in self.raw["global"].get("gray", []):
                if rule_matches(rule, effect):
                    return "gray", f"global.gray: {rule}"
        return "oos", "no rule"
