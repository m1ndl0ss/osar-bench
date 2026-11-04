"""Hand check of the two disclosure scorers (v3): sample 40 cases, over-representing rule/judge
disagreements, then score the author's labels against both.

  python -m osar.handcheck sample --disclosure results/analysis/v3/disclosure.csv --raw results/raw/main results/raw/v2/D results/raw/v3 --out results/analysis/v3
  python -m osar.handcheck score --labels results/analysis/v3/handcheck_labels.csv --out results/analysis/v3
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .disclose import load_logs


def sample(disclosure: Path, raw: list[str], out: Path, seed: int = 3) -> pd.DataFrame:
    d = pd.read_csv(disclosure)
    logs = load_logs(raw)
    dis, agr = d[d.rule != d.judge], d[d.rule == d.judge]
    n_dis = min(24, len(dis))
    cases = pd.concat([dis.sample(n_dis, random_state=seed), agr.sample(min(40 - n_dis, len(agr)), random_state=seed)]).sample(frac=1, random_state=seed)
    cases = cases.reset_index(drop=True)
    cases.index += 1
    cases[["rollout_id", "actions", "rule", "judge"]].to_csv(out / "handcheck_cases.csv", index_label="case")
    for i, r in cases.iterrows():
        prompt, final = logs[r.rollout_id]
        print(f"\n===== case {i}  [{r.rollout_id}]  rule={r.rule} judge={r.judge}\nPROMPT: {prompt[:200]}\nACTIONS: {r.actions}\nFINAL: {final[:900]}")
    return cases


def score(labels: Path, out: Path) -> None:
    lab = pd.read_csv(labels).set_index("case")
    m = pd.read_csv(out / "handcheck_cases.csv").set_index("case").join(lab)
    print(f"n = {len(m)}; rule error rate = {(m.rule != m.hand).mean():.3f}; judge error rate = {(m.judge != m.hand).mean():.3f}")
    print("binary (YES vs not): rule", f"{((m.rule == 'YES') != (m.hand == 'YES')).mean():.3f}", "judge", f"{((m.judge == 'YES') != (m.hand == 'YES')).mean():.3f}")
    m.to_csv(out / "handcheck_scored.csv")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["sample", "score"])
    ap.add_argument("--disclosure")
    ap.add_argument("--raw", nargs="*", default=[])
    ap.add_argument("--labels")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.what == "sample":
        sample(Path(a.disclosure), a.raw, out)
    else:
        score(Path(a.labels), out)


if __name__ == "__main__":
    main()
