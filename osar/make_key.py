"""Regenerate the answer keys of the coding sheets from committed data (the keys stay out of git).

  python -m osar.make_key            # writes prereg/coding_sheet_KEY.csv and prereg/coding_sheet_v4_KEY.csv
  python -m osar.make_key --check    # regenerates into a temp dir and compares with the committed sheets and the stored sha256

v1 key: osar.kappa.export on results/scored/main, n = 200, seed 7.
v4 key: osar.packet.build on results/scored/v2, v3 and v4 with prereg/tasks_v4.yaml, n = 300, seed 11.
The suspicion hand-check sheet has no key: its labels are made by hand.
Expected sha256 of each key is in prereg/coding_sheet_KEY.sha256 and prereg/coding_sheet_v4_KEY.sha256.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path

from .kappa import export
from .packet import build
from .rubric import Rubric

ROOT = Path(__file__).resolve().parent.parent
SCORED = [str(ROOT / d) for d in ("results/scored/v2", "results/scored/v3", "results/scored/v4")]
FILES = ("coding_sheet.csv", "coding_sheet_v4.csv", "coding_sheet_KEY.csv", "coding_sheet_v4_KEY.csv")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    export(ROOT / "results/scored/main", 200, out_dir / "coding_sheet.csv", seed=7)
    sheet, key = build(SCORED, Rubric.load(ROOT / "prereg/tasks_v4.yaml"), 300, 11)
    sheet.to_csv(out_dir / "coding_sheet_v4.csv", index=False)
    key.to_csv(out_dir / "coding_sheet_v4_KEY.csv", index=False)


def expected(name: str) -> str | None:
    """sha256 to compare with: the stored hash for a key, the committed file for a sheet"""
    stored = ROOT / "prereg" / name.replace(".csv", ".sha256")
    if name.endswith("_KEY.csv") and stored.exists():
        return stored.read_text().split()[0]
    ref = ROOT / "prereg" / name
    return sha256(ref) if ref.exists() else None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if not a.check:
        make(ROOT / "prereg")
        for k in ("coding_sheet_KEY.csv", "coding_sheet_v4_KEY.csv"):
            print(k, sha256(ROOT / "prereg" / k))
        return
    tmp = Path(tempfile.mkdtemp())
    make(tmp)
    ok = True
    for name in FILES:
        want = expected(name)
        if want is None:
            print(name, "nothing to compare with")
            continue
        same = sha256(tmp / name) == want
        ok &= same
        print(name, "identical" if same else "DIFFERENT")
    shutil.rmtree(tmp)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
