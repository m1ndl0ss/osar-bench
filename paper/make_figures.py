"""Redraw the paper's figures from the analysis CSVs with plain model labels.
    python paper/make_figures.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from osar.analyze import INK, INK2, _style  # noqa: E402

OUT = ROOT / "paper/figures"
MODEL = {"claude-haiku-5-5": "Haiku", "claude-sonnet-5-5": "Sonnet", "claude-opus-5-5": "Opus"}
MODELS = list(MODEL)
C_FRAMING = {"tight": "#52514e", "loose": "#c43c1b"}
C_ARM = {"base_tight": "#52514e", "base_loose": "#9a9890", "D": "#eda100", "E1a": "#2a78d6", "E1b": "#104281",
         "E2": "#eb6834", "E3": "#c43c1b", "E4": "#4ea36a", "F1": "#c43c1b", "F2": "#eb6834"}
OUTCOMES = ["escalated", "workaround", "plain_in_scope", "asked_stopped", "other"]
C_OUT = {"escalated": "#c43c1b", "workaround": "#eda100", "plain_in_scope": "#9a9890", "asked_stopped": "#2a78d6", "other": "#52514e"}


def fig1():
    s = pd.read_csv(ROOT / "results/analysis/main/summary.csv")
    metrics = [("any_oos", "any out-of-scope action"), ("any_sensitive_oos", "a sensitive one"), ("any_consequential_oos", "a consequential one")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for ax, (col, name) in zip(axes, metrics):
        for i, m in enumerate(MODELS):
            for j, fr in enumerate(("tight", "loose")):
                r = s[(s.metric == col) & (s.model == m) & (s.framing == fr)].iloc[0]
                y = i + (0.18 if fr == "loose" else -0.18)
                ax.hlines(y, r.ci_lo, r.ci_hi, color=C_FRAMING[fr], linewidth=2.5)
                ax.plot(r.estimate, y, "o", color=C_FRAMING[fr], markersize=7, markeredgecolor="white", markeredgewidth=1.5,
                        label=fr if (i == 0 and col == "any_oos") else None)
        ax.set_xlim(-0.03, 1.0)
        ax.set_title(name, loc="left", color=INK, fontsize=11)
        ax.set_xlabel("share of rollouts (95% CI)", color=INK2, fontsize=9)
        _style(ax)
    axes[0].set_yticks(range(len(MODELS)), [MODEL[m] for m in MODELS], color=INK, fontsize=11)
    axes[0].invert_yaxis()
    axes[0].legend(frameon=False, fontsize=9, loc="lower right", title="prompt", title_fontsize=9)
    fig.suptitle("v1: out-of-scope rollouts by model and prompt framing", x=0.01, ha="left", color=INK, fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_osar_by_model.png", dpi=220)
    plt.close(fig)


def forest():
    d = pd.read_csv(ROOT / "results/analysis/integrated/forest_per_task.csv")
    d["t"] = d.task_id.str.split("_").str[0].str[1:].astype(int)
    d = d.sort_values("t")
    fig, ax = plt.subplots(figsize=(8, 6))
    for i, r in enumerate(d.itertuples()):
        ax.hlines(i, r.ci_lo, r.ci_hi, color="#c43c1b", linewidth=2)
        ax.plot(r.effect, i, "o", color="#c43c1b", markersize=6, markeredgecolor="white", markeredgewidth=1.5)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_yticks(range(len(d)), [t.replace("_", " ") for t in d.task_id], color=INK, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("loose minus tight, share of rollouts with any out-of-scope action (95% CI, all models pooled)", color=INK2, fontsize=9)
    ax.set_title("Framing effect per task", loc="left", color=INK, fontsize=12)
    _style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig_int_1_forest.png", dpi=220)
    plt.close(fig)


def fig_v3():
    rt = pd.read_csv(ROOT / "results/analysis/v3/rates_by_arm.csv")
    arms = [a for a in C_ARM if a in set(rt.arm) and not a.startswith("F")]
    metrics = [("any_escalation", "any sudo or chmod/chown"), ("any_consequential_oos", "a consequential out-of-scope effect")]
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 0.42 * len(arms) * len(MODELS) + 3))
    labels = [f"{MODEL[m]}  ·  {a}" for m in MODELS for a in arms]
    for ax, (col, name) in zip(axes, metrics):
        for i, (m, a) in enumerate((m, a) for m in MODELS for a in arms):
            s = rt[(rt.model == m) & (rt.arm == a) & (rt.metric == col)]
            if not len(s):
                ax.text(0.0, i, "not run", color=INK2, fontsize=9, va="center")
                continue
            ax.hlines(i, s.ci_lo.iloc[0], s.ci_hi.iloc[0], color=C_ARM[a], linewidth=2)
            ax.plot(s.estimate.iloc[0], i, "o", color=C_ARM[a], markersize=6, markeredgecolor="white", markeredgewidth=1.5)
        ax.set_xlim(-0.03, 1.02)
        ax.set_title(name, loc="left", color=INK, fontsize=11)
        ax.set_xlabel("share of rollouts (95% CI)", color=INK2, fontsize=9)
        ax.set_yticks(range(len(labels)), labels, color=INK, fontsize=9)
        ax.invert_yaxis()
        _style(ax)
    fig.suptitle("v3: escalation and consequential out-of-scope rate by arm (friction tasks)", x=0.01, ha="left", color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "fig_v3_1_escalation.png", dpi=220)
    plt.close(fig)


def fig_v4():
    tab = pd.read_csv(ROOT / "results/analysis/v4/outcomes_by_arm.csv")
    arms = [a for a in ("D", "F1", "F2") if a in set(tab.arm)]
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(arms) * len(MODELS) + 1.6))
    labels, y = [], 0
    for m in MODELS:
        for a in arms:
            s = tab[(tab.model == m) & (tab.arm == a)]
            if not len(s):
                continue
            left = 0.0
            for o in OUTCOMES:
                v = float(s[o].iloc[0])
                ax.barh(y, v, left=left, color=C_OUT[o], height=0.7, label=o.replace("_", " ") if y == 0 else None)
                left += v
            labels.append(f"{MODEL[m]}  ·  {a}")
            y += 1
    ax.set_yticks(range(len(labels)), labels, color=INK, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of rollouts", color=INK2, fontsize=9)
    ax.legend(frameon=False, fontsize=8, ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    _style(ax)
    fig.suptitle("Outcome under one-off (D) and persistent (F1, F2) denial", x=0.01, ha="left", color=INK, fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "fig_v4_1_outcomes.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig1()
    forest()
    fig_v3()
    fig_v4()
    print("figures written to", OUT)
