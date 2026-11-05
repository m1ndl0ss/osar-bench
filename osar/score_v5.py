"""Re-score raw logs under rubric v5 (prereg/tasks_v5.yaml, osar/rubric_v5.py); the frozen scorer is reused as is.

  python -m osar.score_v5 --raw results/raw/main --out results/scored_v5/main
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .rubric_v5 import RubricV5
from .score import ROOT, score


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", default=str(ROOT / "prereg/tasks_v5.yaml"))
    ap.add_argument("--raw", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rubric = RubricV5.load(a.rubric)
    eff, rol = score(rubric, [Path(r) for r in a.raw])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    eff.to_csv(out / "effects.csv", index=False)
    rol.to_csv(out / "rollouts.csv", index=False)
    print(f"scored {len(rol)} rollouts, {len(eff)} effects under v5 -> {out}")


if __name__ == "__main__":
    main()
