"""Agreement between the three model raters and the scorer on the v1-v4 coding sheet.

  python -m osar.agreement --key prereg/coding_sheet_v4_KEY.csv --raters results/analysis/supplementary/rater_v4_*.csv \
      --out results/analysis/supplementary

Cohen's kappa of each rater against the scorer (ruled items only; unclassified commands have no scorer label),
pairwise Cohen's kappa between raters (all items), Fleiss' kappa across the three (all items), the majority
vote against the scorer (ties counted as disagreements and also excluded), and disagreements by item type.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.inter_rater import fleiss_kappa

LABELS = ["in_scope", "gray", "oos"]


def majority(row) -> str:
    c = Counter(row).most_common()
    return c[0][0] if len(c) == 1 or c[0][1] > c[1][1] else "tie"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--raters", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    key = pd.read_csv(a.key).set_index("item")
    raters = {}
    for f in a.raters:
        name = Path(f).stem.replace("rater_v4_", "")
        raters[name] = pd.read_csv(f).set_index("item").label.reindex(key.index)
    r = pd.DataFrame(raters)
    ok = r.notna().all(axis=1) & r.isin(LABELS).all(axis=1)
    r, k = r[ok], key[ok]
    ruled = k.label.isin(LABELS)
    res = {"items": int(len(r)), "ruled_items": int(ruled.sum())}
    res["kappa_vs_scorer"] = {n: float(cohen_kappa_score(k.label[ruled], r[n][ruled])) for n in r}
    res["agreement_vs_scorer"] = {n: float((k.label[ruled] == r[n][ruled]).mean()) for n in r}
    names = list(r)
    res["pairwise_kappa"] = {f"{x} vs {y}": float(cohen_kappa_score(r[x], r[y])) for i, x in enumerate(names) for y in names[i + 1:]}
    counts = np.array([[(r.loc[i] == lab).sum() for lab in LABELS] for i in r.index])
    res["fleiss_kappa"] = float(fleiss_kappa(counts))
    res["fleiss_kappa_ruled_items"] = float(fleiss_kappa(counts[ruled.values]))
    mv = r.apply(majority, axis=1)
    res["majority_ties"] = int((mv == "tie").sum())
    res["majority_vs_scorer_kappa_ties_excluded"] = float(cohen_kappa_score(k.label[ruled & (mv != "tie")], mv[ruled & (mv != "tie")]))
    res["majority_vs_scorer_agreement_ties_as_disagreement"] = float((mv[ruled] == k.label[ruled]).mean())
    rows = []
    for stratum, g in k.groupby("stratum"):
        rr = r.loc[g.index]
        row = {"item_type": stratum, "n": len(g), "all_three_agree": float((rr.nunique(axis=1) == 1).mean())}
        if g.label.isin(LABELS).any():
            gg = g[g.label.isin(LABELS)]
            row["majority_matches_scorer"] = float((mv[gg.index] == gg.label).mean())
            for n in names:
                row[f"{n}_matches_scorer"] = float((rr.loc[gg.index, n] == gg.label).mean())
        rows.append(row)
    by_type = pd.DataFrame(rows)
    lab_counts = {n: r[n].value_counts().to_dict() for n in names}
    unk = k[~ruled]
    res["unclassified_labels_by_rater"] = {n: r.loc[unk.index, n].value_counts().to_dict() for n in names}
    out = Path(a.out)
    (out / "agreement_v4.json").write_text(json.dumps(res, indent=1))
    by_type.round(3).to_csv(out / "agreement_v4_by_type.csv", index=False)
    pd.concat([k[["label", "stratum"]], r], axis=1).to_csv(out / "agreement_v4_items.csv")
    print(json.dumps(res, indent=1))
    print(by_type.round(3).to_string(index=False))
    print("label counts:", lab_counts)


if __name__ == "__main__":
    main()
