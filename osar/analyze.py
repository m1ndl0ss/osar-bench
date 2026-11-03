"""Pre-registered analysis: rates with task-stratified cluster bootstrap CIs, the
framing contrast (H2/H2b) per model and pooled with Holm correction, pairwise model
contrasts (H3), robustness checks, exploratory metrics, measured cost, figures.

  python -m osar.analyze --scored results/scored/main --out results/analysis/main
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
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
    "any_unclassified": "Any unmodelled shell command (reported separately)",
    "clarification": "Ended by asking a question, not completed (exploratory)",
}
PRIMARY = ("any_oos", "any_consequential_oos")
CLAUDE = ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5")

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


def holm(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, in the original order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def ci(d: np.ndarray) -> tuple[float, float]:
    return float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))


def summarize(rol: pd.DataFrame, B: int, rng: np.random.Generator):
    """Per model x framing: every metric, plus the primary metrics among completed rollouts."""
    rows, draws = [], {}
    for (model, fr), g in rol.groupby(["model", "framing"]):
        for col in METRICS:
            d = boot(g, col, B, rng)
            draws[(model, fr, col)] = d
            rows.append({"model": model, "framing": fr, "metric": col, "n_rollouts": len(g),
                         "n_tasks": g.task_id.nunique(), "estimate": macro_rate(g, col),
                         "ci_lo": ci(d)[0], "ci_hi": ci(d)[1]})
        done = g[g.completed]
        for col in PRIMARY:
            if len(done):
                d = boot(done, col, B, rng)
                rows.append({"model": model, "framing": fr, "metric": f"{col}|completed", "n_rollouts": len(done),
                             "n_tasks": done.task_id.nunique(), "estimate": macro_rate(done, col),
                             "ci_lo": ci(d)[0], "ci_hi": ci(d)[1]})
    return pd.DataFrame(rows), draws


def framing_contrasts(rol: pd.DataFrame, draws: dict, B: int, rng: np.random.Generator, metrics) -> pd.DataFrame:
    """H2: loose minus tight per model and pooled over models (tasks as strata).
    One-sided p = share of bootstrap draws at or below zero; Holm over the per-model tests."""
    rows = []
    for col in metrics:
        for model in sorted(rol.model.unique()):
            if (model, "tight", col) not in draws or (model, "loose", col) not in draws:
                continue
            diff = draws[(model, "loose", col)] - draws[(model, "tight", col)]
            sub = rol[rol.model == model]
            est = macro_rate(sub[sub.framing == "loose"], col) - macro_rate(sub[sub.framing == "tight"], col)
            rows.append({"model": model, "metric": col, "loose_minus_tight": est,
                         "ci_lo": ci(diff)[0], "ci_hi": ci(diff)[1],
                         "p_one_sided": float((diff <= 0).mean()),
                         "p_two_sided": min(1.0, 2 * min((diff <= 0).mean(), (diff >= 0).mean()))})
        if rol.model.nunique() > 1:
            diff = boot(rol[rol.framing == "loose"], col, B, rng) - boot(rol[rol.framing == "tight"], col, B, rng)
            est = macro_rate(rol[rol.framing == "loose"], col) - macro_rate(rol[rol.framing == "tight"], col)
            rows.append({"model": "pooled", "metric": col, "loose_minus_tight": est,
                         "ci_lo": ci(diff)[0], "ci_hi": ci(diff)[1],
                         "p_one_sided": float((diff <= 0).mean()),
                         "p_two_sided": min(1.0, 2 * min((diff <= 0).mean(), (diff >= 0).mean()))})
    out = pd.DataFrame(rows)
    out["p_holm"] = np.nan
    for col in metrics:
        per_model = out[(out.metric == col) & (out.model != "pooled")].index
        if len(per_model):
            out.loc[per_model, "p_holm"] = holm(list(out.loc[per_model, "p_one_sided"]))
    return out


def model_contrasts(rol: pd.DataFrame, B: int, rng: np.random.Generator) -> pd.DataFrame:
    """H3: pairwise differences between the Claude tiers, both framings pooled, Holm over the pairs."""
    models = [m for m in CLAUDE if m in set(rol.model)]
    if len(models) < 2:
        models = sorted(rol.model.unique())
    rows = []
    for col in PRIMARY:
        d = {m: boot(rol[rol.model == m], col, B, rng) for m in models}
        est = {m: macro_rate(rol[rol.model == m], col) for m in models}
        for a, b in combinations(models, 2):
            diff = d[b] - d[a]
            rows.append({"pair": f"{b} - {a}", "metric": col, "difference": est[b] - est[a],
                         "ci_lo": ci(diff)[0], "ci_hi": ci(diff)[1],
                         "p_two_sided": min(1.0, 2 * min((diff <= 0).mean(), (diff >= 0).mean()))})
    out = pd.DataFrame(rows)
    if len(out):
        out["p_holm"] = np.nan
        for col in PRIMARY:
            idx = out[out.metric == col].index
            out.loc[idx, "p_holm"] = holm(list(out.loc[idx, "p_two_sided"]))
    return out


def leave_one_task_out(rol: pd.DataFrame, B: int, rng: np.random.Generator) -> pd.DataFrame:
    """Robustness: the pooled framing contrast with each task left out in turn."""
    rows = []
    for task in sorted(rol.task_id.unique()):
        sub = rol[rol.task_id != task]
        for col in PRIMARY:
            loose, tight = sub[sub.framing == "loose"], sub[sub.framing == "tight"]
            diff = boot(loose, col, B, rng) - boot(tight, col, B, rng)
            rows.append({"task_left_out": task, "metric": col,
                         "loose_minus_tight": macro_rate(loose, col) - macro_rate(tight, col),
                         "ci_lo": ci(diff)[0], "ci_hi": ci(diff)[1]})
    return pd.DataFrame(rows)


def mixed_model(rol: pd.DataFrame, col: str) -> str:
    """Robustness: logistic mixed model  metric ~ framing * model + (1 | task)."""
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    data = rol[["task_id", "framing", "model", col]].copy()
    data[col] = data[col].astype(int)
    try:
        fit = BinomialBayesMixedGLM.from_formula(f"{col} ~ framing * model", {"task": "0 + C(task_id)"}, data).fit_vb()
        return f"{col} ~ framing * model + (1 | task), variational Bayes fit\n{fit.summary()}"
    except Exception as e:  # noqa: BLE001 - a cell with no events can make the fit fail
        return f"{col}: the mixed model did not fit ({e!r})"


def cost_table(rol: pd.DataFrame) -> pd.DataFrame:
    out = []
    for model, g in rol.groupby("model"):
        p = PRICES.get(model)
        tok = g[["tok_input", "tok_output", "tok_cache_read", "tok_cache_write", "tok_thinking"]].mean()
        usd = (None if p is None else
               (tok.tok_input * p[0] + tok.tok_output * p[1] + tok.tok_cache_read * p[2]
                + tok.tok_cache_write * p[3]) / 1e6)
        out.append({"model": model, "rollouts": len(g), **tok.round(0).to_dict(),
                    "usd_per_rollout": usd, "usd_total": None if usd is None else usd * len(g)})
    return pd.DataFrame(out)


def unclassified_summary(eff: pd.DataFrame) -> pd.DataFrame:
    u = eff[eff.label == "unclassified"].copy()
    if not len(u):
        return pd.DataFrame(columns=["model", "framing", "n_effects", "n_rollouts", "commands"])
    u["command"] = u.meta.map(lambda m: json.loads(m).get("command", "")).str.split().str[0]
    return (u.groupby(["model", "framing"])
            .agg(n_effects=("op", "size"), n_rollouts=("rollout_id", "nunique"),
                 commands=("command", lambda c: ", ".join(sorted(set(c)))))
            .reset_index())


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
    for ax, col in zip(axes, PRIMARY):
        s = summary[summary.metric == col]
        for fr, c, dy in (("tight", C_TIGHT, -0.12), ("loose", C_LOOSE, 0.12)):
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


def write_report(out: Path, note: str, summary, h2, h3, strict, loto, mixed, costs, uncl):
    def table(df):
        return df.round(3).to_markdown(index=False) if len(df) else "(none)"

    piv = summary[summary.metric.isin(["any_oos", "any_consequential_oos", "completed"])].copy()
    piv["value"] = piv.apply(lambda r: f"{r.estimate:.2f} [{r.ci_lo:.2f}, {r.ci_hi:.2f}]", axis=1)
    expl = summary[summary.metric.isin(["clarification", "any_unclassified", "any_oos|completed",
                                        "any_consequential_oos|completed"])].copy()
    expl["value"] = expl.apply(lambda r: f"{r.estimate:.2f} [{r.ci_lo:.2f}, {r.ci_hi:.2f}]", axis=1)
    with open(out / "report.md", "w") as f:
        f.write(f"# OSAR analysis{note}\n\n")
        f.write("## Primary metrics (task-macro-averaged share of rollouts, 95% bootstrap CI)\n\n")
        f.write(piv.pivot_table(index=["model", "framing"], columns="metric", values="value",
                                aggfunc="first").to_markdown() + "\n\n")
        f.write("## H2 / H2b: loose minus tight (one-sided p; Holm over the per-model tests)\n\n" + table(h2) + "\n\n")
        f.write("## H3: pairwise model differences, both framings pooled (two-sided p; Holm over the pairs)\n\n"
                + table(h3) + "\n\n")
        f.write("## Exploratory: clarification, unmodelled commands, OOS among completed rollouts\n\n")
        f.write(expl.pivot_table(index=["model", "framing"], columns="metric", values="value",
                                 aggfunc="first").to_markdown() + "\n\n")
        f.write("## Unclassified effects (unmodelled shell commands, coded by hand)\n\n" + table(uncl) + "\n\n")
        f.write("## Robustness: strict labelling (gray counted as out of scope)\n\n" + table(strict) + "\n\n")
        f.write("## Robustness: leave one task out (pooled contrast)\n\n" + table(loto) + "\n\n")
        f.write("## Robustness: logistic mixed model\n\n```\n" + "\n\n".join(mixed) + "\n```\n\n")
        f.write("## Measured cost\n\n" + costs.round(4).to_markdown(index=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261102)
    ap.add_argument("--note", default="", help="text appended to figure titles, e.g. ' (DRY RUN)'")
    a = ap.parse_args(argv)
    sd, out = Path(a.scored), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rol = pd.read_csv(sd / "rollouts.csv")
    eff = pd.read_csv(sd / "effects.csv")
    rol = rol[rol.status != "error"]
    rng = np.random.default_rng(a.seed)
    summary, draws = summarize(rol, a.boot, rng)
    h2 = framing_contrasts(rol, draws, a.boot, rng, PRIMARY)
    h3 = model_contrasts(rol, a.boot, rng)
    strict = framing_contrasts(rol, draws, a.boot, rng, ("any_oos_strict", "any_oos_nonnav"))
    loto = leave_one_task_out(rol, a.boot, rng)
    mixed = [mixed_model(rol, col) for col in PRIMARY]
    costs = cost_table(rol)
    uncl = unclassified_summary(eff)
    summary.to_csv(out / "summary.csv", index=False)
    h2.to_csv(out / "framing_contrasts.csv", index=False)
    h3.to_csv(out / "model_contrasts.csv", index=False)
    strict.to_csv(out / "robustness_strict.csv", index=False)
    loto.to_csv(out / "robustness_loto.csv", index=False)
    (out / "mixed_model.txt").write_text("\n\n".join(mixed))
    costs.to_csv(out / "cost.csv", index=False)
    uncl.to_csv(out / "unclassified_summary.csv", index=False)
    eff[eff.label == "unclassified"].to_csv(out / "needs_human_review.csv", index=False)
    fig_rates(summary, out / "fig1_osar_by_model.png", a.note)
    fig_severity(eff, rol, out / "fig2_severity.png", a.note)
    fig_task_heat(rol, out / "fig3_task_heatmap.png", a.note)
    write_report(out, a.note, summary, h2, h3, strict, loto, mixed, costs, uncl)
    print(json.dumps({"rollouts": len(rol), "unclassified_effects": int((eff.label == "unclassified").sum()),
                      "out": str(out)}))


if __name__ == "__main__":
    main()
