"""Build the LaTeX tables of the paper from the analysis CSVs.
    python paper/make_tables.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "paper/tables"
MODEL = {"claude-haiku-5-5": "Haiku", "claude-sonnet-5-5": "Sonnet", "claude-opus-5-5": "Opus", "pooled": "pooled"}


def tex(s: str) -> str:
    s = str(s).replace("\\", "/").replace("&", "\\&").replace("#", "\\#").replace("$", "\\$").replace("~", "\\textasciitilde{}")
    s = s.replace("_", "\\_").replace("%", "\\%").replace(">", "$>$").replace("<", "$<$").replace("`", "'")
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
             "Arm & Model & flagged & real (incl. collateral) & unrequested & privileged & collateral & blocked/no-op only \\\\", "\\midrule"]
    for r in d.sort_values(["arm", "model"]).itertuples():
        lines.append(f"{tex(r.arm)} & {MODEL[r.model]} & {r.any_consequential:.3f} & {r.real:.3f} & {r.unrequested:.3f} & "
                     f"{r.privileged:.3f} & {r.collateral:.3f} & {r.blocked_only:.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "categories.tex").write_text("\n".join(lines) + "\n")


def prompts():
    import yaml
    tasks = yaml.safe_load(open(ROOT / "prereg/tasks_v4.yaml"))["tasks"]
    lines = ["\\begin{longtable}{lp{6.3cm}p{6.3cm}}",
             "\\caption{All 23 tasks with their tight and loose prompts, as in \\code{prereg/tasks\\_v4.yaml}.}\\label{tab:prompts} \\\\",
             "\\toprule", "Task & Tight prompt & Loose prompt \\\\", "\\midrule", "\\endfirsthead",
             "\\caption*{Table~\\thetable{} (continued)} \\\\", "\\toprule", "Task & Tight prompt & Loose prompt \\\\", "\\midrule", "\\endhead"]
    for t in tasks:
        tight, loose = (tex(t['prompts'][k]).replace('/', '/\\allowbreak{}') for k in ('tight', 'loose'))
        lines.append(f"{tex(t['id'].split('_')[0])} & {tight} & {loose} \\\\[2pt]")
    lines += ["\\bottomrule", "\\end{longtable}"]
    (OUT / "prompts.tex").write_text("\n".join(lines) + "\n")


def unclassified():
    from osar.refine import load_scored
    rol, eff = load_scored([str(ROOT / d) for d in ("results/scored/v2", "results/scored/v3", "results/scored/v4")])
    arm = rol.set_index("rollout_id").arm
    arm = arm.replace({"friction_persistent": "F1", "friction_persistent_scope": "F2"})
    e = eff.assign(arm=eff.rollout_id.map(arm))
    tot = e.groupby(["arm", "model"]).size()
    unk = e[e.op == "exec_unknown"].groupby(["arm", "model"]).size().reindex(tot.index, fill_value=0)
    roll = e[e.op == "exec_unknown"].groupby(["arm", "model"]).rollout_id.nunique().reindex(tot.index, fill_value=0)
    n_roll = rol.assign(arm=rol.arm.replace({"friction_persistent": "F1", "friction_persistent_scope": "F2"})).groupby(["arm", "model"]).size()
    lines = ["\\begin{tabular}{llrrrr}", "\\toprule", "Arm & Model & effects & unclassified & share & rollouts with one \\\\", "\\midrule"]
    for (a, m), n in tot.items():
        lines.append(f"{tex(a)} & {MODEL[m]} & {n} & {unk[(a, m)]} & {unk[(a, m)] / n:.3f} & {roll[(a, m)] / n_roll[(a, m)]:.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "unclassified.tex").write_text("\n".join(lines) + "\n")


def outcome_cis():
    d = pd.read_csv(ROOT / "results/analysis/v4/rates_by_arm.csv")
    cols = ["escalate_exec", "escalate_probe", "workaround", "asked_stopped", "completed"]
    lines = ["\\begin{tabular}{ll" + "r" * len(cols) + "}", "\\toprule", "Arm & Model & " + " & ".join(tex(c) for c in cols) + " \\\\", "\\midrule"]
    for (a, m), g in d.groupby(["arm", "model"]):
        cells = []
        for c in cols:
            r = g[g.metric == c].iloc[0]
            cells.append(f"{r.estimate:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]")
        lines.append(f"{a} & {MODEL[m]} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "outcomes_v4_ci.tex").write_text("\n".join(lines) + "\n")


def sensitivity():
    d = pd.read_csv(ROOT / "results/analysis/refined/sensitivity_real_change.csv")
    names = {"any_consequential_oos": "registered", "real_change": "real change", "unrequested": "unrequested"}
    lines = ["\\begin{tabular}{lllrrrr}", "\\toprule", "Test & Model & Outcome & rate a & rate b & difference [95\\% CI] & one-sided $p$ \\\\", "\\midrule"]
    for r in d.itertuples():
        lines.append(f"{r.hypothesis} {tex(r.contrast)} & {MODEL[r.model]} & {names[r.metric]} & {r.rate_a:.3f} & {r.rate_b:.3f} & "
                     f"{r.difference:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}] & {r.p_one_sided:.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "sensitivity.tex").write_text("\n".join(lines) + "\n")


def comparison():
    d = pd.read_csv(ROOT / "results/analysis_v5/comparison_v4_v5.csv")
    order = {f"H{i}": i for i in range(1, 14)}
    order.update({"H2b": 2.5, "H4a": 4.1, "H4b": 4.2, "H4c": 4.3})
    d["k"] = d.hypothesis.map(order)
    d = d.sort_values("k", kind="stable")
    lines = ["\\begin{tabular}{lp{5.2cm}llllc}", "\\toprule", "ID & Claim & Verdict (orig.) & Effect (orig.) & Verdict (v5) & Effect (v5) & Changed \\\\", "\\midrule"]
    for r in d.itertuples():
        def eff(e, lo, hi):
            return f"{e:+.3f}" if pd.isna(lo) else f"{e:+.3f} [{lo:+.3f}, {hi:+.3f}]"
        flag = "verdict" if r.verdict_changed else ("effect" if r.effect_moved else "")
        lines.append(f"{r.hypothesis} & {tex(r.claim)} & {tex(r.verdict_orig)} & {eff(r.effect_orig, r.ci_lo_orig, r.ci_hi_orig)} & {tex(r.verdict_v5)} & {eff(r.effect_v5, r.ci_lo_v5, r.ci_hi_v5)} & {flag} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "comparison_v5.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    consolidated()
    outcomes()
    categories()
    prompts()
    unclassified()
    outcome_cis()
    sensitivity()
    comparison()
    print("tables written to", OUT)
