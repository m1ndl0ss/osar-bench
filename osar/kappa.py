"""Inter-rater agreement on effect labels.

1) Export a stratified, shuffled sample for blind human coding (automatic label hidden):
     python -m osar.kappa export --scored results/scored/main --n 200 --out prereg/coding_sheet.csv
   Give each rater the CSV plus prereg/tasks_v0.yaml (the rubric) and CODING_GUIDE in
   PREREGISTRATION.md. Raters fill `label` with in_scope / gray / oos.
2) Compute agreement:
     python -m osar.kappa compute --key prereg/coding_key.csv rater1.csv rater2.csv
   Reports Cohen's kappa for rater1-vs-rater2 and each rater vs the deterministic scorer.
3) Sensitivity analysis (pre-registered): count unclassified effects a rater coded as oos
     python -m osar.kappa sensitivity --scored results/scored/main --key prereg/coding_sheet_KEY.csv rater1.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).resolve().parent.parent


def export(scored: Path, n: int, out: Path, seed: int = 7):
    import yaml
    eff = pd.read_csv(scored / "effects.csv")
    tasks = {t["id"]: t for t in yaml.safe_load(open(ROOT / "prereg/tasks_v1.yaml"))["tasks"]}
    # oversample the rare labels so kappa is not dominated by easy in-scope cases
    per = max(1, n // 3)
    ruled = eff[eff.label != "unclassified"]
    parts = [g.sample(min(len(g), per), random_state=seed) for _, g in ruled.groupby("label")]
    parts.append(eff[eff.label == "unclassified"])  # every unmodelled command is coded by hand
    s = pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    s["item"] = range(1, len(s) + 1)
    s["prompt"] = [tasks[t]["prompts"][f] for t, f in zip(s.task_id, s.framing)]
    sheet = s[["item", "task_id", "framing", "prompt", "tool", "op", "target", "meta"]].copy()
    sheet["label"] = ""
    sheet["note"] = ""
    sheet.to_csv(out, index=False)
    s[["item", "label", "severity", "rule", "rollout_id"]].to_csv(out.with_name(out.stem + "_KEY.csv"), index=False)
    print(f"wrote {len(sheet)} items to {out}, {int((s.label == 'unclassified').sum())} of them unclassified "
          f"(key: {out.stem}_KEY.csv, do not share with raters)")


def macro(rol, col):
    return rol.groupby(["model", "framing", "task_id"])[col].mean().groupby(["model", "framing"]).mean()


def sensitivity(scored: Path, key: Path, rater: Path):
    """Pre-registered sensitivity analysis: unclassified effects that the rater
    coded as oos are added to any_oos / any_oos_nonnav of their rollout."""
    k = pd.read_csv(key).set_index("item")
    r = pd.read_csv(rater).set_index("item")["label"].str.strip().str.lower()
    items = r[r == "oos"].index.intersection(k.index)
    flipped = set(k.loc[items][k.loc[items].label == "unclassified"].rollout_id)
    rol = pd.read_csv(scored / "rollouts.csv")
    before = macro(rol, "any_oos")
    rol.loc[rol.rollout_id.isin(flipped), ["any_oos", "any_oos_nonnav"]] = True
    after = macro(rol, "any_oos")
    table = pd.DataFrame({"any_oos": before, "any_oos_with_coded_unclassified": after})
    print(f"{len(flipped)} rollouts gain an oos effect from human coding")
    print(table.round(3).to_string())
    rol.to_csv(scored / "rollouts_sensitivity.csv", index=False)


def compute(key: Path, raters: list[Path]):
    k = pd.read_csv(key).set_index("item")
    rs = [pd.read_csv(r).set_index("item")["label"].str.strip().str.lower() for r in raters]
    res = {}
    for i, r in enumerate(rs, 1):
        common = r.dropna().index.intersection(k.index)
        res[f"rater{i}_vs_scorer"] = cohen_kappa_score(r[common], k.loc[common, "label"])
    if len(rs) == 2:
        common = rs[0].dropna().index.intersection(rs[1].dropna().index)
        res["rater1_vs_rater2"] = cohen_kappa_score(rs[0][common], rs[1][common])
        res["n_items"] = len(common)
        dis = common[rs[0][common] != rs[1][common]]
        res["disagreements"] = [int(x) for x in dis]
    print(json.dumps(res, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export"); e.add_argument("--scored", required=True)
    e.add_argument("--n", type=int, default=200); e.add_argument("--out", required=True)
    c = sub.add_parser("compute"); c.add_argument("--key", required=True); c.add_argument("raters", nargs="+")
    s = sub.add_parser("sensitivity"); s.add_argument("--scored", required=True)
    s.add_argument("--key", required=True); s.add_argument("rater")
    a = ap.parse_args(argv)
    if a.cmd == "export":
        export(Path(a.scored), a.n, Path(a.out))
    elif a.cmd == "compute":
        compute(Path(a.key), [Path(r) for r in a.raters])
    else:
        sensitivity(Path(a.scored), Path(a.key), Path(a.rater))


if __name__ == "__main__":
    main()
