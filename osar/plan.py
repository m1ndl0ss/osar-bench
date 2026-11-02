"""Sampling and budget plan from pilot data.

  python -m osar.plan --scored results/scored/pilot --ledger results/spend_ledger.jsonl

Prints three things:
  (a) cost per rollout per model, from the spend ledger (mean and 90th percentile)
  (b) rollouts per cell (task x framing x model) needed to detect a 10-point
      loose-vs-tight difference at 80% power, alpha 0.05 one- and two-sided
  (c) a budget table: Haiku + Sonnet at that n, Opus at 0 / 5 / 10 per cell

The variance of a task-macro-averaged rate with n rollouts per task is
sum_t p_t(1-p_t) / (T^2 n). The loose-minus-tight contrast sums the two cells.
Tasks with no pilot data use p = 0.5 (the worst case).
"""
from __future__ import annotations

import argparse
import json
from math import ceil
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from .pricing import usd
from .rubric import Rubric

ROOT = Path(__file__).resolve().parent.parent
Z_ALPHA = {"one-sided": 1.6449, "two-sided": 1.9600}
Z_POWER = 0.8416  # 80%
FRAMINGS = ("tight", "loose")


def load_rollouts(dirs: list[str]) -> pd.DataFrame:
    frames = [pd.read_csv(Path(d) / "rollouts.csv") for d in dirs if (Path(d) / "rollouts.csv").exists()]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_ledger(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame(columns=["model", "usd", "ok"])
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["model", "usd", "ok"])


def cost_per_rollout(ledger: pd.DataFrame, rol: pd.DataFrame, assumed: dict) -> dict:
    """model -> {mean, p90, n, source}. The ledger wins; otherwise the token
    columns of the scored CSV priced at list rates; otherwise --assume-usd."""
    out = {}
    for model, g in ledger[ledger.ok == True].groupby("model"):  # noqa: E712
        out[model] = {"mean": g.usd.mean(), "p90": g.usd.quantile(0.9), "n": len(g), "source": "ledger"}
    for model, g in rol.groupby("model") if len(rol) else []:
        if model in out:
            continue
        c = [usd(model, {"input": r.tok_input, "output": r.tok_output,
                         "cache_read": r.tok_cache_read, "cache_write": r.tok_cache_write})
             for r in g.itertuples()]
        if any(c):
            out[model] = {"mean": float(np.mean(c)), "p90": float(np.quantile(c, 0.9)),
                          "n": len(c), "source": "tokens x list price"}
    for model, c in assumed.items():
        out.setdefault(model, {"mean": c, "p90": c, "n": 0, "source": "assumed"})
    return out


def task_rates(rol: pd.DataFrame, tasks: list[str], metric: str) -> dict:
    """task -> (p_tight, p_loose); 0.5 where there is no pilot data."""
    rates = {}
    for t in tasks:
        pair = []
        for fr in FRAMINGS:
            g = rol[(rol.task_id == t) & (rol.framing == fr)] if len(rol) else rol
            pair.append(float(g[metric].mean()) if len(g) else 0.5)
        rates[t] = tuple(pair)
    return rates


def n_per_cell(rates: dict, delta: float, sides: str) -> int:
    """Rollouts per task x framing so that loose - tight = delta is detected
    with 80% power at alpha 0.05."""
    T = len(rates)
    v = sum(p * (1 - p) for pair in rates.values() for p in pair) / T ** 2
    if v == 0:
        return 1
    return int(ceil((Z_ALPHA[sides] + Z_POWER) ** 2 * v / delta ** 2))


def parse_assumed(text: str) -> dict:
    out = {}
    for part in text.split(","):
        if part.strip():
            model, value = part.split("=")
            out[model.strip()] = float(value)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", nargs="+", default=[str(ROOT / "results/scored/pilot")])
    ap.add_argument("--ledger", default=str(ROOT / "results/spend_ledger.jsonl"))
    ap.add_argument("--rubric", default=str(ROOT / "prereg/tasks_v0.yaml"))
    ap.add_argument("--metric", default="any_oos", help="rollout-level flag used for the power calculation")
    ap.add_argument("--delta", type=float, default=0.10, help="loose minus tight difference to detect")
    ap.add_argument("--haiku", default="claude-haiku-5-5")
    ap.add_argument("--sonnet", default="claude-sonnet-5-5")
    ap.add_argument("--opus", default="claude-opus-5-5")
    ap.add_argument("--assume-usd", default="", help="per-rollout cost for models with no data, e.g. m1=0.02,m2=0.1")
    a = ap.parse_args(argv)

    tasks = list(Rubric.load(a.rubric).tasks)
    rol = load_rollouts(a.scored)
    ledger = load_ledger(a.ledger)
    costs = cost_per_rollout(ledger, rol, parse_assumed(a.assume_usd))
    roles = {"haiku": a.haiku, "sonnet": a.sonnet, "opus": a.opus}
    cells = len(tasks) * len(FRAMINGS)

    print(f"(a) cost per rollout  [{len(ledger)} ledger entries, "
          f"{len(rol)} scored rollouts, {len(tasks)} tasks]")
    rows = [[m, f"{c['mean']:.4f}", f"{c['p90']:.4f}", c["n"], c["source"]] for m, c in sorted(costs.items())]
    print(tabulate(rows, headers=["model", "mean usd", "p90 usd", "n", "source"]) if rows else "  no cost data")
    spent = float(ledger.usd.sum()) if len(ledger) else 0.0
    print(f"  ledger total so far: ${spent:.4f}\n")

    print(f"(b) rollouts per cell to detect a {a.delta:.0%} loose-vs-tight difference "
          f"(80% power, alpha 0.05); metric {a.metric}, p=0.5 where no data")
    groups = {"haiku": [a.haiku], "sonnet": [a.sonnet], "opus": [a.opus],
              "pooled haiku+sonnet": [a.haiku, a.sonnet]}
    need = {}
    rows = []
    for name, models in groups.items():
        sub = rol[rol.model.isin(models)] if len(rol) else rol
        with_data = sub.task_id.nunique() if len(sub) else 0
        n = {}
        for sides in Z_ALPHA:
            rates = task_rates(sub, tasks, a.metric)
            # the pooled contrast has every model's rollouts in each task x framing
            n[sides] = ceil(n_per_cell(rates, a.delta, sides) / len(models))
        need[name] = n
        rows.append([name, with_data, len(sub), n["one-sided"], n["two-sided"]])
    print(tabulate(rows, headers=["group", "tasks with data", "pilot rollouts",
                                  "n/cell one-sided", "n/cell two-sided"]))
    print("  (pooled row: n per model cell; the pooled test uses both models' rollouts)\n")

    print(f"(c) budget: Haiku + Sonnet at the required n per cell ({cells} cells each), "
          f"Opus at 0 / 5 / 10 per cell; mean cost per rollout")
    rows = []
    for sides in Z_ALPHA:
        n_hs = max(need["haiku"][sides], need["sonnet"][sides])
        for n_opus in (0, 5, 10):
            parts = {}
            for role, n in (("haiku", n_hs), ("sonnet", n_hs), ("opus", n_opus)):
                c = costs.get(roles[role])
                parts[role] = None if c is None else n * cells * c["mean"]
            if any(v is None for v in parts.values()):
                total = None
            else:
                total = sum(parts.values())
            flag = ""
            if total is not None:
                if spent + total > 50:
                    flag = "OVER $50 HARD CAP"
                elif spent + total > 40:
                    flag = "over $40"
            fmt = lambda v: "n/a" if v is None else f"{v:.2f}"  # noqa: E731
            rows.append([sides, n_hs, n_opus, fmt(parts["haiku"]), fmt(parts["sonnet"]), fmt(parts["opus"]),
                         fmt(total), fmt(None if total is None else spent + total), flag])
    print(tabulate(rows, headers=["alpha", "n/cell H+S", "n/cell Opus", "haiku $", "sonnet $",
                                  "opus $", "planned $", "with spent $", "flag"]))
    missing = [roles[r] for r in roles if roles[r] not in costs]
    if missing:
        print(f"  no cost data for {missing}: pass --assume-usd or run a pilot first")


if __name__ == "__main__":
    main()
