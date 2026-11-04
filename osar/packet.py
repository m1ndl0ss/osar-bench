"""Rater packet: one blind coding sheet over v1-v4 (at most 300 effects).

  python -m osar.packet --scored results/scored/v2 results/scored/v3 results/scored/v4 \
      --rubric prereg/tasks_v4.yaml --out prereg/coding_sheet_v4.csv

Items: one representative per distinct unclassified shell command, every real privileged
edit (sudo that changed state), every email sent on T7, and a stratified sample of the
other labelled effects (label x severity x version). The answer key goes to a *_KEY.csv
next to the sheet, which is git-ignored. Raters fill `label` with in_scope / gray / oos.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .categories import annotate, initial_dirs
from .refine import load_scored
from .rubric import Rubric

VERSION = {"B": "v2", "C": "v2", "D": "v2", "E1a": "v3", "E1b": "v3", "E2": "v3", "E3": "v3", "E4": "v3",
           "friction_persistent": "v4", "friction_persistent_scope": "v4"}


def version_of(arm: str, task_id: str) -> str:
    if arm.startswith("base"):
        return "v1" if int(task_id[1:].split("_")[0]) <= 11 else "v2"
    return VERSION.get(arm, "v2")


def build(scored: list[str], rubric: Rubric, n: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rol, eff = load_scored(scored)
    rol["version"] = [version_of(a, t) for a, t in zip(rol.arm, rol.task_id)]
    ann = annotate(eff, initial_dirs(rubric.raw["base_files"]))
    ann = ann.merge(rol[["rollout_id", "version"]], on="rollout_id")
    # fixed strata: every distinct unmodelled command once, every privileged edit, every T7 email
    unk = ann[ann.op == "exec_unknown"]
    one_each = unk.loc[[g.sample(1, random_state=seed).index[0] for _, g in unk.groupby("target")]]
    fixed = pd.concat([one_each.assign(stratum="unclassified"),
                       ann[(ann.op == "escalate") & (ann.kind == "exec")].assign(stratum="privileged edit"),
                       ann[(ann.op == "message") & (ann.task_id == "T7_meeting_todos")].assign(stratum="T7 email")])
    # the rest: equal shares per label x severity x version cell, topped up at random
    rest = ann[(ann.label != "unclassified") & ~ann.index.isin(fixed.index)]
    cells = [g for _, g in rest.groupby(["label", "severity", "version"])]
    per = max(1, (n - len(fixed)) // len(cells))
    picked = pd.concat([g.sample(min(len(g), per), random_state=seed) for g in cells])
    short = n - len(fixed) - len(picked)
    if short > 0:
        pool = rest[~rest.index.isin(picked.index)]
        picked = pd.concat([picked, pool.sample(min(short, len(pool)), random_state=seed)])
    items = pd.concat([fixed, picked.assign(stratum="sample")]).sample(frac=1, random_state=seed).reset_index(drop=True)
    items["item"] = range(1, len(items) + 1)
    items["prompt"] = [rubric.tasks[t]["prompts"][f] for t, f in zip(items.task_id, items.framing)]
    items["command"] = [json.loads(m).get("command", "") if isinstance(m, str) else "" for m in items.meta]
    sheet = items[["item", "version", "task_id", "framing", "condition", "prompt", "tool", "op", "target", "command"]].copy()
    sheet["denied"] = ["yes" if d else "" for d in items.denied]
    sheet["label"] = ""
    sheet["note"] = ""
    key = items[["item", "label", "severity", "rule", "rollout_id", "stratum", "kind", "category", "privileged", "noop"]]
    return sheet, key


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", nargs="+", required=True)
    ap.add_argument("--rubric", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args(argv)
    out = Path(a.out)
    sheet, key = build(a.scored, Rubric.load(a.rubric), a.n, a.seed)
    sheet.to_csv(out, index=False)
    key.to_csv(out.with_name(out.stem + "_KEY.csv"), index=False)
    print(f"wrote {len(sheet)} items to {out}; strata: {key.stratum.value_counts().to_dict()}; "
          f"labels in key: {key.label.value_counts().to_dict()} (key: {out.stem}_KEY.csv, not for raters)")


if __name__ == "__main__":
    main()
