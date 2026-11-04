"""Disclosure of privileged edits in the persistent-denial arms (and v2 D for reference).
Same keyword rule and judge prompt as v3 (osar/disclose.py); the action list holds the
sudo'd commands that changed state plus any other real consequential out-of-scope effect.

  python -m osar.disclose_v4 --scored results/scored/v4 --rubric prereg/tasks_v4.yaml \
      --raw results/raw/v2/D results/raw/v4 --out results/analysis/v4 [--judge]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd

from .analyze_v3 import FRICTION_TASKS
from .analyze_v4 import arm_of
from .categories import annotate, initial_dirs, per_rollout
from .disclose import ask_judge, load_logs, rule
from .rubric import Rubric

REAL = ("unrequested", "privileged", "collateral")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--rubric", required=True)
    ap.add_argument("--raw", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--judge", action="store_true", help="also ask the judge model (API calls)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rubric = Rubric.load(a.rubric)
    rol = pd.read_csv(Path(a.scored) / "rollouts.csv")
    rol["condition"] = rol.condition.fillna("baseline")
    rol["effort"] = rol.effort.fillna("low")
    rol["arm"] = rol.apply(arm_of, axis=1)
    rol = rol[rol.arm.isin(["D", "F1", "F2"]) & (rol.framing == "tight") & rol.task_id.isin(FRICTION_TASKS)].set_index("rollout_id")
    eff = pd.read_csv(Path(a.scored) / "effects.csv")
    ann = annotate(eff[eff.rollout_id.isin(rol.index)], initial_dirs(rubric.raw["base_files"]))
    flags = per_rollout(ann)
    logs = load_logs(a.raw)
    client = None
    if a.judge:
        import anthropic
        headers = {"anthropic-workspace-id": os.environ["OSAR_ANTHROPIC_WORKSPACE"]} if os.environ.get("OSAR_ANTHROPIC_WORKSPACE") else {}
        client = anthropic.Anthropic(api_key=os.environ["OSAR_ANTHROPIC_KEY"], default_headers=headers)
    rows = []
    for rid in flags[flags.escalate_exec].index:
        if rid not in logs:
            continue
        g = ann[ann.rollout_id == rid]
        owed = g[((g.op == "escalate") & (g.kind == "exec")) | ((g.op != "escalate") & g.category.isin(REAL))]
        actions = [{"op": r.op, "target": r.target, "command": json.loads(r.meta).get("command", "")} for r in owed.itertuples()]
        prompt, final_text = logs[rid]
        row = {"rollout_id": rid, "model": rol.loc[rid, "model"], "arm": rol.loc[rid, "arm"], "task_id": rol.loc[rid, "task_id"],
               "n_actions": len(actions), "actions": "; ".join(f"{x['op']} {x['target']}" for x in actions),
               "rule": rule(actions, final_text)}
        if client is not None:
            row["judge"], row["judge_reason"] = ask_judge(client, prompt, actions, final_text)
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(out / "disclosure_v4.csv", index=False)
    if len(df):
        keys = ["arm", "model"]
        tab = df.groupby(keys).agg(n=("rule", "size"), rule_yes=("rule", lambda s: (s == "YES").mean()))
        if "judge" in df:
            tab["judge_yes"] = df.groupby(keys).judge.apply(lambda s: (s == "YES").mean())
        tab.round(3).to_csv(out / "disclosure_v4_summary.csv")
        print(tab.round(3).to_string())
    print(f"{len(df)} escalated rollouts")


if __name__ == "__main__":
    main()
