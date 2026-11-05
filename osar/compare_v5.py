"""One table: every hypothesis under the original rubric and under v5, with changed verdicts flagged.

  python -m osar.compare_v5 --orig results/analysis/integrated/consolidated_table.csv \
      --v5 results/analysis_v5/integrated/consolidated_table.csv --out results/analysis_v5
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", required=True)
    ap.add_argument("--v5", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    o = pd.read_csv(a.orig).rename(columns={"verdict": "verdict_orig", "effect": "effect_orig", "ci_lo": "ci_lo_orig", "ci_hi": "ci_hi_orig"})
    v = pd.read_csv(a.v5).rename(columns={"verdict": "verdict_v5", "effect": "effect_v5", "ci_lo": "ci_lo_v5", "ci_hi": "ci_hi_v5"})
    m = o.merge(v.drop(columns=["addendum"]), on=["hypothesis", "claim"], how="outer")
    m["verdict_changed"] = m.verdict_orig != m.verdict_v5
    m["effect_moved"] = (m.effect_orig - m.effect_v5).abs() > 0.0005
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    m.to_csv(out / "comparison_v4_v5.csv", index=False)
    lines = ["# H1-H13 under the original rubric and under v5", "", "| ID | claim | verdict (orig) | effect (orig) | verdict (v5) | effect (v5) | changed |", "|---|---|---|---|---|---|---|"]
    for r in m.itertuples():
        ci = lambda e, lo, hi: f"{e:+.3f}" if pd.isna(lo) else f"{e:+.3f} [{lo:+.3f}, {hi:+.3f}]"  # noqa: E731
        lines.append(f"| {r.hypothesis} | {r.claim} | {r.verdict_orig} | {ci(r.effect_orig, r.ci_lo_orig, r.ci_hi_orig)} | {r.verdict_v5} | {ci(r.effect_v5, r.ci_lo_v5, r.ci_hi_v5)} | {'VERDICT' if r.verdict_changed else ('effect' if r.effect_moved else '')} |")
    (out / "comparison_v4_v5.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nverdicts changed: {int(m.verdict_changed.sum())}; effects moved: {int(m.effect_moved.sum())}")


if __name__ == "__main__":
    main()
