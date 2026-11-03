"""Pre-registered analysis of the v2 addendum (H4-H7). Reads one scored directory
that holds the v1 baseline rollouts (condition "baseline") together with the v2
runs (new tasks under "baseline", and the ask_user / scope_instruction /
friction conditions).

  python -m osar.analyze_v2 --scored results/scored/v2 --out results/analysis/v2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .analyze import (C_LOOSE, C_TIGHT, CLAUDE, GRID, INK, INK2, PRIMARY, _style, boot, ci,  # noqa: E402
                      fig_rates, framing_contrasts, holm, macro_rate, summarize)

C_COND = {"baseline": "#52514e", "ask_user": "#2a78d6", "scope_instruction": "#eb6834", "friction": "#eda100"}
EXTRA = ("completed", "clarification", "any_ask_user", "any_oos_nonnav")


def task_number(task_id: str) -> int:
    return int(task_id[1:].split("_")[0])


def condition_contrast(rol, cond, framing, tasks, metrics, B, rng, predicted):
    """condition minus baseline on the same tasks and framing. `predicted` is the
    direction the hypothesis expects: "lower", "higher" or "none" (two-sided only)."""
    base = rol[(rol.condition == "baseline") & (rol.framing == framing) & rol.task_id.isin(tasks)]
    trt = rol[(rol.condition == cond) & (rol.framing == framing) & rol.task_id.isin(tasks)]
    rows = []
    for col in metrics:
        for model in sorted(trt.model.unique()) + ["pooled"]:
            b = base if model == "pooled" else base[base.model == model]
            t = trt if model == "pooled" else trt[trt.model == model]
            if not len(b) or not len(t):
                continue
            d = boot(t, col, B, rng) - boot(b, col, B, rng)
            p_two = min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))
            p_one = float((d >= 0).mean()) if predicted == "lower" else float((d <= 0).mean())
            rows.append({"condition": cond, "framing": framing, "model": model, "metric": col,
                         "n_baseline": len(b), "n_condition": len(t),
                         "baseline": macro_rate(b, col), "with_condition": macro_rate(t, col),
                         "difference": macro_rate(t, col) - macro_rate(b, col),
                         "ci_lo": ci(d)[0], "ci_hi": ci(d)[1],
                         "p_one_sided": p_one if predicted != "none" else np.nan, "p_two_sided": p_two})
    out = pd.DataFrame(rows)
    if len(out):
        out["p_holm"] = np.nan
        for col in metrics:
            idx = out[(out.metric == col) & (out.model != "pooled")].index
            if predicted != "none" and len(idx):
                out.loc[idx, "p_holm"] = holm(list(out.loc[idx, "p_one_sided"]))
    return out


def h4c(rol, B, rng):
    """Opus consequential OOS under loose framing on the new tasks exceeds Haiku and Sonnet."""
    sub = rol[(rol.condition == "baseline") & (rol.framing == "loose") & (rol.task_id.map(task_number) >= 12)]
    col = "any_consequential_oos"
    d = {m: boot(sub[sub.model == m], col, B, rng) for m in CLAUDE if m in set(sub.model)}
    if "claude-opus-5-5" not in d:
        return pd.DataFrame()
    rows = []
    for other in ("claude-haiku-5-5", "claude-sonnet-5-5"):
        if other not in d:
            continue
        diff = d["claude-opus-5-5"] - d[other]
        rows.append({"pair": f"claude-opus-5-5 - {other}", "metric": col,
                     "difference": macro_rate(sub[sub.model == "claude-opus-5-5"], col) - macro_rate(sub[sub.model == other], col),
                     "ci_lo": ci(diff)[0], "ci_hi": ci(diff)[1], "p_one_sided": float((diff <= 0).mean())})
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(list(out.p_one_sided))
    return out


def escalation_table(rol):
    f = rol[rol.condition == "friction"]
    if not len(f):
        return pd.DataFrame()
    g = f.groupby("model")
    return pd.DataFrame({
        "rollouts": g.size(),
        "denied_once": g.n_denied.apply(lambda s: (s > 0).mean()),
        "share_sudo": g.n_escalate.apply(lambda s: (s > 0).mean()),
        "share_chmod_chown": g.n_perm.apply(lambda s: (s > 0).mean()),
        "share_gave_up": g.apply(lambda x: ((x.n_denied > 0) & ~x.completed).mean()),
        "completed": g.completed.mean(),
    }).reset_index()


def fig_conditions(rates, path, note):
    """Dots with CIs: baseline vs each condition, per model, for the two primary metrics."""
    rows = [("loose", "baseline"), ("loose", "ask_user"), ("loose", "scope_instruction"),
            ("tight", "baseline"), ("tight", "friction")]
    models = [m for m in CLAUDE if m in set(rates.model)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.55 * len(rows) * len(models) / 2 + 2.2), sharey=True)
    labels = [f"{m.replace('claude-', '')}  ·  {fr}  ·  {c}" for m in models for fr, c in rows]
    for ax, col in zip(axes, PRIMARY):
        for i, (m, (fr, c)) in enumerate((m, r) for m in models for r in rows):
            s = rates[(rates.model == m) & (rates.framing == fr) & (rates.condition == c) & (rates.metric == col)]
            if not len(s):
                continue
            ax.hlines(i, s.ci_lo.iloc[0], s.ci_hi.iloc[0], color=C_COND[c], linewidth=2)
            ax.plot(s.estimate.iloc[0], i, "o", color=C_COND[c], markersize=7, markeredgecolor="white", markeredgewidth=1.5)
        ax.set_xlim(-0.03, 1.02)
        ax.set_title(col.replace("_", " "), loc="left", color=INK, fontsize=10)
        ax.set_xlabel("share of rollouts (95% CI, task-stratified bootstrap)", color=INK2, fontsize=8)
        _style(ax)
    axes[0].set_yticks(range(len(labels)), labels, color=INK, fontsize=7)
    axes[0].invert_yaxis()
    fig.suptitle(f"Baseline vs conditions, all tasks{note}", x=0.01, ha="left", color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def rate_table(rol, B, rng):
    rows = []
    for (cond, model, fr), g in rol.groupby(["condition", "model", "framing"]):
        for col in PRIMARY + EXTRA:
            d = boot(g, col, B, rng)
            rows.append({"condition": cond, "model": model, "framing": fr, "metric": col, "n_rollouts": len(g),
                         "n_tasks": g.task_id.nunique(), "estimate": macro_rate(g, col), "ci_lo": ci(d)[0], "ci_hi": ci(d)[1]})
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261104)
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rol = pd.read_csv(Path(a.scored) / "rollouts.csv")
    rol = rol[rol.status != "error"].copy()
    rol["condition"] = rol.condition.fillna("baseline")
    rng = np.random.default_rng(a.seed)
    new = rol[rol.task_id.map(task_number) >= 12]
    old = rol[rol.task_id.map(task_number) <= 11]
    all_tasks = sorted(rol.task_id.unique())
    friction_tasks = sorted(rol[rol.condition == "friction"].task_id.unique())

    # H4: the new tasks under the baseline harness
    base_new = new[new.condition == "baseline"]
    summary_new, draws = summarize(base_new, a.boot, rng)
    h4 = framing_contrasts(base_new, draws, a.boot, rng, PRIMARY)
    h4c_tab = h4c(rol, a.boot, rng)
    # H5, H6: loose framing, all tasks; H7: tight framing, friction tasks
    h5 = condition_contrast(rol, "ask_user", "loose", all_tasks, PRIMARY, a.boot, rng, "lower")
    h5_extra = condition_contrast(rol, "ask_user", "loose", all_tasks, ("completed", "any_ask_user"), a.boot, rng, "none")
    h6 = condition_contrast(rol, "scope_instruction", "loose", all_tasks, PRIMARY, a.boot, rng, "lower")
    h6_extra = condition_contrast(rol, "scope_instruction", "loose", all_tasks, ("completed", "clarification"), a.boot, rng, "none")
    h7 = condition_contrast(rol, "friction", "tight", friction_tasks, PRIMARY, a.boot, rng, "higher")
    h7_extra = condition_contrast(rol, "friction", "tight", friction_tasks, ("completed",), a.boot, rng, "none")
    esc = escalation_table(rol)
    rates = rate_table(rol, a.boot, rng)

    summary_new.to_csv(out / "h4_rates_new_tasks.csv", index=False)
    h4.to_csv(out / "h4ab_framing_contrasts.csv", index=False)
    h4c_tab.to_csv(out / "h4c_opus_vs_others.csv", index=False)
    pd.concat([h5, h5_extra]).to_csv(out / "h5_ask_user.csv", index=False)
    pd.concat([h6, h6_extra]).to_csv(out / "h6_scope_instruction.csv", index=False)
    pd.concat([h7, h7_extra]).to_csv(out / "h7_friction.csv", index=False)
    esc.to_csv(out / "h7_escalation.csv", index=False)
    rates.to_csv(out / "rates_by_condition.csv", index=False)
    if len(summary_new):
        fig_rates(summary_new, out / "fig_v2_1_new_tasks.png", f" (new tasks T12-T23{a.note})")
    fig_conditions(rates, out / "fig_v2_2_conditions.png", a.note)

    def table(df):
        return df.round(3).to_markdown(index=False) if len(df) else "(none)"
    with open(out / "report.md", "w") as f:
        f.write(f"# OSAR v2 addendum analysis{a.note}\n\n")
        piv = summary_new[summary_new.metric.isin(["any_oos", "any_consequential_oos", "completed"])].copy()
        if len(piv):
            piv["value"] = piv.apply(lambda r: f"{r.estimate:.2f} [{r.ci_lo:.2f}, {r.ci_hi:.2f}]", axis=1)
            f.write("## New tasks T12-T23, baseline harness (task-macro-averaged share of rollouts, 95% CI)\n\n")
            f.write(piv.pivot_table(index=["model", "framing"], columns="metric", values="value", aggfunc="first").to_markdown() + "\n\n")
        f.write("## H4a / H4b: loose minus tight on the new tasks (one-sided p; Holm over the per-model tests)\n\n" + table(h4) + "\n\n")
        f.write("## H4c: Opus minus others, consequential OOS, loose framing, new tasks (one-sided; Holm)\n\n" + table(h4c_tab) + "\n\n")
        f.write("## H5: ask_user vs baseline, loose framing, all tasks (predicted lower; one-sided p; Holm)\n\n" + table(h5) + "\n\n")
        f.write("Ask rate and completion under ask_user (two-sided):\n\n" + table(h5_extra) + "\n\n")
        f.write("## H6: scope instruction vs baseline, loose framing, all tasks (predicted lower; one-sided p; Holm)\n\n" + table(h6) + "\n\n")
        f.write("Cost of the instruction: completion and clarification rate (two-sided):\n\n" + table(h6_extra) + "\n\n")
        f.write(f"## H7: friction vs baseline, tight framing, tasks {', '.join(friction_tasks)} (predicted higher; one-sided p; Holm)\n\n" + table(h7) + "\n\n")
        f.write("Completion under friction (two-sided):\n\n" + table(h7_extra) + "\n\n")
        f.write("Escalation under friction (share of rollouts):\n\n" + table(esc) + "\n\n")
        f.write("## Rates by condition\n\n" + table(rates) + "\n")
    print(json.dumps({"rollouts": len(rol), "conditions": sorted(rol.condition.unique()), "out": str(out)}))


if __name__ == "__main__":
    main()
