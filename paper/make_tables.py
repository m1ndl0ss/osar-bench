"""Build the LaTeX tables of the paper from the analysis CSVs.
    python paper/make_tables.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper/tables"
MODEL = {"claude-haiku-5-5": "Haiku", "claude-sonnet-5-5": "Sonnet", "claude-opus-5-5": "Opus", "pooled": "pooled"}


def tex(s: str) -> str:
    s = str(s).replace("_", "\\_").replace("%", "\\%").replace(">", "$>$").replace("<", "$<$")
    for k, v in MODEL.items():
        s = s.replace(k, v)
    return s


def consolidated():
    d = pd.read_csv(ROOT / "results/analysis/integrated/consolidated_table.csv")
    order = {f"H{i}": i for i in range(1, 14)}
    order.update({"H2b": 2.5, "H4a": 4.1, "H4b": 4.2, "H4c": 4.3})
    d["k"] = d.hypothesis.map(order)
    d = d.sort_values("k", kind="stable")
    lines = ["\\begin{tabular}{llp{6.6cm}lr}", "\\toprule", "ID & Add. & Claim & Verdict & Effect [95\\% CI] \\\\", "\\midrule"]
    for r in d.itertuples():
        if pd.isna(r.ci_lo):
            eff = f"{r.effect:.3f}"
        else:
            eff = f"{r.effect:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]"
        lines.append(f"{r.hypothesis} & {r.addendum} & {tex(r.claim)} & {tex(r.verdict)} & {eff} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "consolidated.tex").write_text("\n".join(lines) + "\n")


def outcomes():
    d = pd.read_csv(ROOT / "results/analysis/v4/outcomes_by_arm.csv")
    lines = ["\\begin{tabular}{llrrrrrrr}", "\\toprule",
             "Arm & Model & escalated & workaround & plain in scope & asked/stopped & other & probed & completed \\\\", "\\midrule"]
    for r in d.itertuples():
        lines.append(f"{r.arm} & {MODEL[r.model]} & {r.escalated:.3f} & {r.workaround:.3f} & {r.plain_in_scope:.3f} & "
                     f"{r.asked_stopped:.3f} & {r.other:.3f} & {r.probed:.3f} & {r.completed:.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "outcomes_v4.tex").write_text("\n".join(lines) + "\n")


def categories():
    d = pd.read_csv(ROOT / "results/analysis/refined/consequential_categories.csv")
    d = d[d.arm.isin(["base_loose", "D", "E2", "E3", "E4"]) & (d.dataset != "v2") | (d.arm == "D")]
    d = d.drop_duplicates(["arm", "model"])
    lines = ["\\begin{tabular}{llrrrrrr}", "\\toprule",
             "Arm & Model & flagged & real & unrequested & privileged & collateral & blocked/no-op only \\\\", "\\midrule"]
    for r in d.sort_values(["arm", "model"]).itertuples():
        lines.append(f"{tex(r.arm)} & {MODEL[r.model]} & {r.any_consequential:.3f} & {r.real:.3f} & {r.unrequested:.3f} & "
                     f"{r.privileged:.3f} & {r.collateral:.3f} & {r.blocked_only:.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "categories.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    consolidated()
    outcomes()
    categories()
    print("tables written to", OUT)
