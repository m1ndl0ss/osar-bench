"""EXPLORATORY analyses, added after the v1 freeze (see prereg/DEVIATIONS.md).
Nothing here feeds the confirmatory tables in osar/analyze.py.

  python -m osar.explore --scored results/scored/main --out results/analysis/main

1. Consequential out-of-scope rate when a `mkdir` on a directory that already
   existed at the start of the task is ignored (a no-op on a real system).
2. Out-of-scope rates among completed rollouts only.
"""
from __future__ import annotations

import argparse
import posixpath
from pathlib import Path

import numpy as np
import pandas as pd

from .analyze import PRIMARY, boot, ci, macro_rate
from .rubric import Rubric

ROOT = Path(__file__).resolve().parent.parent


def initial_dirs(rubric: Rubric) -> set[str]:
    dirs = set()
    for p in rubric.raw["base_files"]:
        d = posixpath.dirname(p)
        while d and d != "/":
            dirs.add(d)
            d = posixpath.dirname(d)
    return dirs


def consequential_without_noop_mkdir(rol: pd.DataFrame, eff: pd.DataFrame, dirs: set[str]) -> pd.Series:
    """any_consequential_oos recomputed per rollout, ignoring mkdir of a pre-existing directory."""
    o = eff[(eff.label == "oos") & (eff.severity == "consequential")]
    noop = (o.op == "mkdir") & o.target.isin(dirs)
    hit = set(o[~noop].rollout_id)
    return rol.rollout_id.isin(hit)


def rate_rows(rol: pd.DataFrame, col: str, name: str, B: int, rng) -> list[dict]:
    rows = []
    for (model, fr), g in rol.groupby(["model", "framing"]):
        d = boot(g, col, B, rng)
        rows.append({"metric": name, "model": model, "framing": fr, "n_rollouts": len(g),
                     "estimate": macro_rate(g, col), "ci_lo": ci(d)[0], "ci_hi": ci(d)[1]})
    return rows


def contrast_rows(rol: pd.DataFrame, col: str, name: str, B: int, rng) -> list[dict]:
    rows = []
    groups = [(m, rol[rol.model == m]) for m in sorted(rol.model.unique())] + [("pooled", rol)]
    for model, g in groups:
        loose, tight = g[g.framing == "loose"], g[g.framing == "tight"]
        d = boot(loose, col, B, rng) - boot(tight, col, B, rng)
        rows.append({"metric": name, "model": model, "loose_minus_tight": macro_rate(loose, col) - macro_rate(tight, col),
                     "ci_lo": ci(d)[0], "ci_hi": ci(d)[1]})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rubric", default=str(ROOT / "prereg/tasks_v1.yaml"))
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261103)
    a = ap.parse_args(argv)
    sd, out = Path(a.scored), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rol = pd.read_csv(sd / "rollouts.csv")
    eff = pd.read_csv(sd / "effects.csv")
    rol = rol[rol.status != "error"].copy()
    rng = np.random.default_rng(a.seed)

    rol["consequential_excl_noop_mkdir"] = consequential_without_noop_mkdir(rol, eff, initial_dirs(Rubric.load(a.rubric)))
    n_noop = int(((eff.label == "oos") & (eff.op == "mkdir") & eff.target.isin(initial_dirs(Rubric.load(a.rubric)))).sum())
    rates = rate_rows(rol, "consequential_excl_noop_mkdir", "any_consequential_oos excl. no-op mkdir", a.boot, rng)
    contrasts = contrast_rows(rol, "consequential_excl_noop_mkdir", "any_consequential_oos excl. no-op mkdir", a.boot, rng)
    done = rol[rol.completed]
    for col in PRIMARY:
        rates += rate_rows(done, col, f"{col} | completed", a.boot, rng)
        contrasts += contrast_rows(done, col, f"{col} | completed", a.boot, rng)
    rates, contrasts = pd.DataFrame(rates), pd.DataFrame(contrasts)
    rates.to_csv(out / "exploratory_rates.csv", index=False)
    contrasts.to_csv(out / "exploratory_contrasts.csv", index=False)
    with open(out / "exploratory.md", "w") as f:
        f.write("# EXPLORATORY analyses (not pre-registered; the confirmatory tables are in report.md)\n\n")
        f.write(f"No-op `mkdir` effects (directory already existed at the start): {n_noop} out-of-scope consequential effects.\n\n")
        f.write("## Rates (task-macro-averaged share of rollouts, 95% bootstrap CI)\n\n" + rates.round(3).to_markdown(index=False) + "\n\n")
        f.write("## Loose minus tight\n\n" + contrasts.round(3).to_markdown(index=False) + "\n")
    print(f"exploratory: {n_noop} no-op mkdir effects; wrote {out / 'exploratory.md'}")


if __name__ == "__main__":
    main()
