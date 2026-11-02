"""Pre-registered analysis: rates with task-stratified cluster bootstrap CIs, framing
contrast, severity breakdown, measured token cost, figures.

  python -m osar.analyze --scored results/scored/pilot --out results/analysis/pilot
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

from .pricing import PRICES  # noqa: E402

METRICS = {
    "any_oos": "Any out-of-scope action (primary)",
    "any_consequential_oos": "Any consequential out-of-scope action (primary)",
    "any_sensitive_oos": "Any sensitive read out of scope",
    "any_oos_strict": "Any out-of-scope or gray action (strict)",
    "any_oos_nonnav": "Any out-of-scope action other than browsing (list/stat)",
    "completed": "Task completed",
}

# reference palette (dataviz skill, light mode): slot1 blue, slot2 orange, slot3 aqua
C_TIGHT, C_LOOSE = "#2a78d6", "#eb6834"
SEV_COLORS = {"benign": "#2a78d6", "sensitive": "#eda100", "consequential": "#eb6834"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"


def macro_rate(df: pd.DataFrame, col: str) -> float:
    return df.groupby("task_id")[col].mean().mean()


def boot(df: pd.DataFrame, col: str, B: int, rng: np.random.Generator) -> np.ndarray:
    """Task-stratified cluster bootstrap of the task-macro-averaged rollout rate."""
    groups = [g[col].to_numpy(dtype=float) for _, g in df.groupby("task_id")]
    out = np.empty(B)
    for b in range(B):
        out[b] = np.mean([g[rng.integers(0, len(g), len(g))].mean() for g in groups])
    return out


def summarize(rol: pd.DataFrame, B: int, seed: int = 20261102):
    rng = np.random.default_rng(seed)
    rows, contrasts, draws = [], [], {}
    for (model, fr), g in rol.groupby(["model", "framing"]):
        for col in METRICS:
            d = boot(g, col, B, rng)
            draws[(model, fr, col)] = d
            rows.append({"model": model, "framing": fr, "metric": col, "n_rollouts": len(g),
                         "n_tasks": g.task_id.nunique(), "estimate": macro_rate(g, col),
                         "ci_lo": np.quantile(d, 0.025), "ci_hi": np.quantile(d, 0.975)})
    for model in rol.model.unique():
        for col in ("any_oos", "any_consequential_oos"):
            if (model, "tight", col) in draws and (model, "loose", col) in draws:
                diff = draws[(model, "loose", col)] - draws[(model, "tight", col)]
                est = (macro_rate(rol[(rol.model == model) & (rol.framing == "loose")], col)
                       - macro_rate(rol[(rol.model == model) & (rol.framing == "tight")], col))
                contrasts.append({"model": model, "metric": col, "loose_minus_tight": est,
                                  "ci_lo": np.quantile(diff, 0.025), "ci_hi": np.quantile(diff, 0.975),
                                  "boot_p_two_sided": min(1.0, 2 * min((diff <= 0).mean(), (diff >= 0).mean()))})
    return pd.DataFrame(rows), pd.DataFrame(contrasts)


def cost_table(rol: pd.DataFrame) -> pd.DataFrame:
    out = []
    for model, g in rol.groupby("model"):
        p = PRICES.get(model)
        tok = g[["tok_input", "tok_output", "tok_cache_read", "tok_cache_write"]].mean()
        usd = (None if p is None else
               (tok.tok_input * p[0] + tok.tok_output * p[1] + tok.tok_cache_read * p[2]
                + tok.tok_cache_write * p[3]) / 1e6)
        out.append({"model": model, "rollouts": len(g), **tok.round(0).to_dict(),
                    "usd_per_rollout": usd,
                    "usd_per_600_rollouts": None if usd is None else usd * 600})
    return pd.DataFrame(out)


def _style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_rates(summary: pd.DataFrame, path: Path, title_note: str):
    models = sorted(summary.model.unique())
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.6 * len(models) + 1.8), sharey=True)
    for ax, col in zip(axes, ("any_oos", "any_consequential_oos")):
        s = summary[summary.metric == col]
        for j, (fr, c, dy) in enumerate((("tight", C_TIGHT, -0.12), ("loose", C_LOOSE, 0.12))):
            ss = s[s.framing == fr].set_index("model").reindex(models)
            y = np.arange(len(models)) + dy
            ax.hlines(y, ss.ci_lo, ss.ci_hi, color=c, linewidth=2)
            ax.plot(ss.estimate, y, "o", color=c, markersize=8, markeredgecolor="white",
                    markeredgewidth=2, label=f"{fr} instructions")
        ax.set_xlim(-0.03, 1.02)
        ax.set_title(METRICS[col].replace(" (primary)", ""), color=INK, fontsize=10, loc="left")
        ax.set_xlabel("share of rollouts (95% CI, task-stratified bootstrap)", color=INK2, fontsize=8)
        _style(ax)
    axes[0].set_yticks(range(len(models)), models, color=INK)
    axes[0].invert_yaxis()
    axes[1].legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle(f"Out-of-scope action rate by model and instruction framing{title_note}",
                 x=0.01, ha="left", color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_severity(eff: pd.DataFrame, rol: pd.DataFrame, path: Path, title_note: str):
    o = eff[eff.label == "oos"]
    per = (o.groupby(["model", "framing", "severity"]).size()
           / rol.groupby(["model", "framing"]).size()).rename("per_rollout").reset_index()
    keys = sorted({(m, f) for m, f in zip(rol.model, rol.framing)}, key=lambda k: (k[0], k[1] != "tight"))
    labels = [f"{m}  ·  {f}" for m, f in keys]
    fig, ax = plt.subplots(figsize=(9, 0.42 * len(keys) + 1.6))
    left = np.zeros(len(keys))
    for sev in ("benign", "sensitive", "consequential"):
        vals = np.array([per[(per.model == m) & (per.framing == f) & (per.severity == sev)]
                         .per_rollout.sum() for m, f in keys])
        ax.barh(range(len(keys)), vals, left=left, color=SEV_COLORS[sev], height=0.6,
                edgecolor="white", linewidth=2, label=sev)
        left += vals
    ax.set_yticks(range(len(keys)), labels, color=INK, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("out-of-scope effects per rollout", color=INK2, fontsize=8)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower right", bbox_to_anchor=(1.0, 1.0))
    ax.set_title(f"Severity of out-of-scope actions{title_note}", loc="left", color=INK, fontsize=11, pad=24)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_task_heat(rol: pd.DataFrame, path: Path, title_note: str):
    t = rol.groupby(["model", "task_id"]).any_consequential_oos.mean().unstack()
    fig, ax = plt.subplots(figsize=(1.4 * t.shape[1] + 2.5, 0.5 * t.shape[0] + 1.6))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("seqblue", ["#f4f8fd", "#86b6ef", "#2a78d6", "#104281"])
    ax.imshow(t.values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(t.shape[0]):
        for j in range(t.shape[1]):
            v = t.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if v > 0.55 else INK)
    ax.set_xticks(range(t.shape[1]), [c.split("_", 1)[1].replace("_", " ") for c in t.columns],
                  fontsize=8, color=INK)
    ax.set_yticks(range(t.shape[0]), t.index, fontsize=8, color=INK)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title(f"Share of rollouts with a consequential out-of-scope action, by task{title_note}",
                 loc="left", color=INK, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=5000)
    ap.add_argument("--note", default="", help="text appended to figure titles, e.g. ' (DRY RUN)'")
    a = ap.parse_args(argv)
    sd, out = Path(a.scored), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rol = pd.read_csv(sd / "rollouts.csv")
    eff = pd.read_csv(sd / "effects.csv")
    rol = rol[rol.status != "error"]
    summary, contrasts = summarize(rol, a.boot)
    costs = cost_table(rol)
    summary.to_csv(out / "summary.csv", index=False)
    contrasts.to_csv(out / "framing_contrasts.csv", index=False)
    costs.to_csv(out / "cost.csv", index=False)
    unclassified = eff[eff.severity == "unclassified"]
    unclassified.to_csv(out / "needs_human_review.csv", index=False)
    fig_rates(summary, out / "fig1_osar_by_model.png", a.note)
    fig_severity(eff, rol, out / "fig2_severity.png", a.note)
    fig_task_heat(rol, out / "fig3_task_heatmap.png", a.note)
    with open(out / "report.md", "w") as f:
        f.write(f"# OSAR analysis{a.note}\n\n")
        piv = summary[summary.metric.isin(["any_oos", "any_consequential_oos", "completed"])].copy()
        piv["value"] = piv.apply(lambda r: f"{r.estimate:.2f} [{r.ci_lo:.2f}, {r.ci_hi:.2f}]", axis=1)
        f.write(piv.pivot_table(index=["model", "framing"], columns="metric", values="value",
                                aggfunc="first").to_markdown() + "\n\n")
        f.write("## Framing contrast (loose − tight)\n\n" + contrasts.round(3).to_markdown(index=False) + "\n\n")
        f.write("## Measured cost\n\n" + costs.round(4).to_markdown(index=False) + "\n\n")
        f.write(f"Unclassified effects needing human review: {len(unclassified)}\n")
    print(json.dumps({"rollouts": len(rol), "out": str(out)}))


if __name__ == "__main__":
    main()
