"""Agreement of the rater majority with the v5 scorer on the 300-item sheet (same items, same rater labels).

  python -m osar.sheet_v5 --scored results/scored_v5/v2 results/scored_v5/v3 results/scored_v5/v4 --out results/analysis_v5
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from .refine import load_scored

LABELS = ["in_scope", "gray", "oos"]
RATERS = ["claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5"]


def v5_labels(scored: list[str], sheet: pd.DataFrame, key: pd.DataFrame) -> pd.Series:
    _, eff = load_scored(scored)
    eff["command"] = [json.loads(m).get("command", "") if isinstance(m, str) else "" for m in eff.meta]
    idx = eff.set_index(["rollout_id", "op", "target"])
    out = {}
    for it, r in sheet.iterrows():
        rid = key.loc[it, "rollout_id"]
        try:
            rows = idx.loc[(rid, r.op, r.target)]
        except KeyError:
            out[it] = None
            continue
        rows = rows if isinstance(rows, pd.DataFrame) else rows.to_frame().T
        if r.op == "exec_unknown" and isinstance(r.command, str):
            rows = rows[rows.command == r.command] if (rows.command == r.command).any() else rows
        out[it] = rows.label.iloc[0]
    return pd.Series(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", nargs="+", required=True)
    ap.add_argument("--sheet", default="prereg/coding_sheet_v4.csv")
    ap.add_argument("--key", default="prereg/coding_sheet_v4_KEY.csv")
    ap.add_argument("--raters", default="results/analysis/supplementary/agreement_v4_items.csv")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sheet = pd.read_csv(a.sheet).set_index("item")
    key = pd.read_csv(a.key).set_index("item")
    items = pd.read_csv(a.raters).rename(columns={"Unnamed: 0": "item"}).set_index("item")
    v5 = v5_labels(a.scored, sheet.loc[items.index], key)
    items["label_v5"] = v5
    maj = items[RATERS].apply(lambda row: (lambda c: c[0][0] if len(c) == 1 or c[0][1] > c[1][1] else "tie")(Counter(row).most_common()), axis=1)
    res = {"items": int(len(items)), "v5_label_found": int(v5.notna().sum())}
    for name, lab in (("v4", items.label), ("v5", items.label_v5)):
        ok = lab.isin(LABELS) & (maj != "tie")
        res[f"ruled_items_{name}"] = int(ok.sum())
        res[f"majority_kappa_vs_{name}"] = float(cohen_kappa_score(lab[ok], maj[ok]))
        res[f"majority_agreement_vs_{name}"] = float((lab[ok] == maj[ok]).mean())
        for r in RATERS:
            res[f"{r}_kappa_vs_{name}"] = float(cohen_kappa_score(lab[ok], items[r][ok]))
    both = items.label.isin(LABELS) & items.label_v5.isin(LABELS) & (maj != "tie")
    res["same_items_ruled_under_both"] = int(both.sum())
    res["majority_kappa_vs_v4_same_items"] = float(cohen_kappa_score(items.label[both], maj[both]))
    res["majority_kappa_vs_v5_same_items"] = float(cohen_kappa_score(items.label_v5[both], maj[both]))
    res["labels_changed_by_v5"] = int((items.label != items.label_v5).sum())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "agreement_v5.json").write_text(json.dumps(res, indent=1))
    items.to_csv(out / "agreement_v5_items.csv")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
