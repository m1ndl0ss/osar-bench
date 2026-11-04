"""EXPLORATORY analyses for the v3 addendum (added after the freeze; nothing here
feeds the confirmatory tables in analyze_v3.py).

  python -m osar.explore_v3 --scored results/scored/v3 --analysis results/analysis/v3 --out results/analysis/v3

1. What sudo was used for: a probe (`sudo -n true`, `sudo -v`, `sudo -l`) or a real
   state change (the sudo'd command wrote, deleted, moved or created something), per arm and model.
2. Disclosure rates split by data set: the v1 main run, the v2 friction arm and the v3 arms,
   from disclosure.csv (rule and judge where present).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .analyze_v3 import arm_of

STATE = ("write", "delete", "move", "mkdir")
PROBES = ("true", "-v", "-l", "-n", "id", "whoami", "echo")


def sudo_use(eff: pd.DataFrame, rol: pd.DataFrame) -> pd.DataFrame:
    """per rollout: sudo probed only, or sudo used for a state change"""
    esc = eff[eff.op == "escalate"]
    rows = []
    for rid, g in esc.groupby("rollout_id"):
        used = False
        for r in g.itertuples():
            same_call = eff[(eff.rollout_id == rid) & (eff.step == r.step) & (eff.call_index == r.call_index)]
            if same_call.op.isin(STATE).any():
                used = True
        cmds = sorted({json.loads(m).get("command", "")[:60] for m in g.meta})
        rows.append({"rollout_id": rid, "sudo_probe_only": not used, "sudo_used_for_state_change": used, "commands": " | ".join(cmds)})
    out = pd.DataFrame(rows)
    if len(out):
        out = out.merge(rol[["rollout_id", "model", "arm", "task_id", "completed"]], on="rollout_id")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--analysis", required=True, help="folder holding disclosure.csv")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rol = pd.read_csv(Path(a.scored) / "rollouts.csv")
    rol["condition"] = rol.condition.fillna("baseline")
    rol["effort"] = rol.effort.fillna("low")
    rol["arm"] = rol.apply(arm_of, axis=1)
    eff = pd.read_csv(Path(a.scored) / "effects.csv")
    su = sudo_use(eff, rol)
    lines = ["# EXPLORATORY: what sudo was used for, and disclosure by data set", ""]
    if len(su):
        su.to_csv(out / "sudo_use.csv", index=False)
        n_arm = rol.groupby(["arm", "model"]).size().rename("rollouts")
        tab = (su.groupby(["arm", "model"]).agg(sudo_rollouts=("rollout_id", "size"), probe_only=("sudo_probe_only", "sum"),
                                                 used_for_state_change=("sudo_used_for_state_change", "sum"), completed=("completed", "mean"))
               .join(n_arm).reset_index())
        tab["share_used"] = tab.used_for_state_change / tab.rollouts
        tab.to_csv(out / "sudo_use_summary.csv", index=False)
        lines += ["## sudo: probe versus real use (per arm and model)", "", tab.round(3).to_markdown(index=False), "",
                  "Commands seen (unique, by arm):", ""]
        for arm, g in su.groupby("arm"):
            cmds = pd.Series([c for cs in g.commands for c in cs.split(" | ")]).value_counts().head(8)
            lines += [f"- {arm}: " + "; ".join(f"`{c}` ({n})" for c, n in cmds.items())]
        lines.append("")
    disc = Path(a.analysis) / "disclosure.csv"
    if disc.exists():
        d = pd.read_csv(disc)
        d["condition"] = d.condition.fillna("baseline")
        d["effort"] = d.effort.fillna("low")
        d["arm"] = d.apply(arm_of, axis=1)
        d["dataset"] = d.apply(lambda r: "v1 main" if r.condition == "baseline" else ("v2 D" if r.arm == "D" else "v3 " + r.arm), axis=1)
        agg = {"n": ("rule", "size"), "rule_yes": ("rule", lambda s: (s == "YES").mean()), "rule_any": ("rule", lambda s: (s != "NO").mean())}
        if "judge" in d:
            agg["judge_yes"] = ("judge", lambda s: (s == "YES").mean())
        t = d.groupby(["dataset", "model"]).agg(**agg).reset_index()
        t.to_csv(out / "disclosure_by_dataset.csv", index=False)
        lines += ["## Disclosure by data set (share of rollouts owing a disclosure whose final message gives it)", "",
                  t.round(3).to_markdown(index=False), ""]
    (out / "exploratory_v3.md").write_text("\n".join(lines))
    print(f"wrote {out / 'exploratory_v3.md'}")


if __name__ == "__main__":
    main()
