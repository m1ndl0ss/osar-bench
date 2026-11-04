"""Integrated view across v1, v2 and v3 (added after the v3 freeze; descriptive).

  python -m osar.integrate --out results/analysis/integrated

1. per-task forest plot of the loose minus tight effect on any_oos (baseline, all models pooled)
2. a mixed-effects logistic model  metric ~ framing + friction + model + (1 | task)  on the
   shared conditions (baseline tight/loose on all tasks, friction tight and loose on the eight tasks)
3. one consolidated table with every hypothesis H1-H11, its verdict, effect, CI and addendum
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .analyze import C_LOOSE, INK, INK2, PRIMARY, _style, boot, ci, macro_rate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def load(path):
    p = ROOT / path
    return pd.read_csv(p) if p.exists() else None


def forest(rol, B, rng, path):
    base = rol[rol.condition == "baseline"]
    rows = []
    for task, g in base.groupby("task_id"):
        loose, tight = g[g.framing == "loose"], g[g.framing == "tight"]
        d = np.array([loose.any_oos.to_numpy(float)[rng.integers(0, len(loose), len(loose))].mean()
                      - tight.any_oos.to_numpy(float)[rng.integers(0, len(tight), len(tight))].mean() for _ in range(B)])
        rows.append({"task_id": task, "effect": loose.any_oos.mean() - tight.any_oos.mean(), "ci_lo": ci(d)[0], "ci_hi": ci(d)[1],
                     "n": len(g)})
    df = pd.DataFrame(rows).sort_values("effect")
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(df) + 1.8))
    y = np.arange(len(df))
    ax.hlines(y, df.ci_lo, df.ci_hi, color=C_LOOSE, linewidth=2)
    ax.plot(df.effect, y, "o", color=C_LOOSE, markersize=6, markeredgecolor="white", markeredgewidth=1.5)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_yticks(y, [t.split("_", 1)[1].replace("_", " ") + f"  ({t.split('_')[0]})" for t in df.task_id], fontsize=8, color=INK)
    ax.set_xlabel("loose minus tight, share of rollouts with any out-of-scope action (95% CI, all models pooled)", color=INK2, fontsize=8)
    ax.set_title("Framing effect per task", loc="left", color=INK, fontsize=11)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return df


def mixed(rol, col):
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    d = rol[(rol.condition == "baseline") | ((rol.condition == "friction") & (rol.effort == "low"))].copy()
    d["loose"] = (d.framing == "loose").astype(int)
    d["friction"] = (d.condition == "friction").astype(int)
    d[col] = d[col].astype(int)
    try:
        fit = BinomialBayesMixedGLM.from_formula(f"{col} ~ loose + friction + model", {"task": "0 + C(task_id)"}, d).fit_vb()
        return f"{col} ~ loose + friction + model + (1 | task), n = {len(d)}, variational Bayes\n{fit.summary()}"
    except Exception as e:  # noqa: BLE001
        return f"{col}: the mixed model did not fit ({e!r})"


def verdict(est, lo, hi, predicted):
    if predicted == "higher":
        return "supported" if lo > 0 else "not supported"
    if predicted == "lower":
        return "supported" if hi < 0 else "not supported"
    return "difference" if lo > 0 or hi < 0 else "no difference"


def consolidated():
    rows = []

    def add(h, text, df, sel, predicted, addendum, est="loose_minus_tight"):
        if df is None:
            rows.append({"hypothesis": h, "claim": text, "verdict": "not run", "effect": None, "ci_lo": None, "ci_hi": None, "addendum": addendum})
            return
        s = df
        for k, v in sel.items():
            s = s[s[k] == v]
        if not len(s):
            rows.append({"hypothesis": h, "claim": text, "verdict": "not run", "effect": None, "ci_lo": None, "ci_hi": None, "addendum": addendum})
            return
        r = s.iloc[0]
        rows.append({"hypothesis": h, "claim": text, "verdict": verdict(r[est], r.ci_lo, r.ci_hi, predicted),
                     "effect": round(float(r[est]), 3), "ci_lo": round(float(r.ci_lo), 3), "ci_hi": round(float(r.ci_hi), 3), "addendum": addendum})

    v1s = load("results/analysis/main/summary.csv")
    if v1s is not None:
        c = v1s[(v1s.metric == "any_consequential_oos") & (v1s.framing == "loose")]
        rows.append({"hypothesis": "H1", "claim": "every model has a non-zero consequential OOS rate (descriptive)",
                     "verdict": "supported" if (c.estimate > 0).all() else "not supported",
                     "effect": round(float(c.estimate.min()), 3), "ci_lo": None, "ci_hi": None, "addendum": "v1"})
    v1c = load("results/analysis/main/framing_contrasts.csv")
    add("H2", "loose > tight any_oos (pooled)", v1c, {"model": "pooled", "metric": "any_oos"}, "higher", "v1")
    add("H2b", "loose > tight any_consequential_oos (pooled)", v1c, {"model": "pooled", "metric": "any_consequential_oos"}, "higher", "v1")
    v1m = load("results/analysis/main/model_contrasts.csv")
    if v1m is not None:
        for _, r in v1m[v1m.metric == "any_oos"].iterrows():
            rows.append({"hypothesis": "H3", "claim": f"{r['pair']} differ on any_oos (two-sided)", "verdict": verdict(r.difference, r.ci_lo, r.ci_hi, "none"),
                         "effect": round(r.difference, 3), "ci_lo": round(r.ci_lo, 3), "ci_hi": round(r.ci_hi, 3), "addendum": "v1"})
    v2h4 = load("results/analysis/v2/h4ab_framing_contrasts.csv")
    add("H4a", "new tasks: loose > tight any_oos (pooled)", v2h4, {"model": "pooled", "metric": "any_oos"}, "higher", "v2")
    add("H4b", "new tasks: loose > tight any_consequential_oos (pooled)", v2h4, {"model": "pooled", "metric": "any_consequential_oos"}, "higher", "v2")
    v2h4c = load("results/analysis/v2/h4c_opus_vs_others.csv")
    if v2h4c is not None:
        for _, r in v2h4c.iterrows():
            rows.append({"hypothesis": "H4c", "claim": f"new tasks, loose: {r['pair']} consequential (one-sided)", "verdict": verdict(r.difference, r.ci_lo, r.ci_hi, "higher"),
                         "effect": round(r.difference, 3), "ci_lo": round(r.ci_lo, 3), "ci_hi": round(r.ci_hi, 3), "addendum": "v2"})
    for h, f, text in (("H5", "h5_ask_user.csv", "ask_user lowers"), ("H6", "h6_scope_instruction.csv", "scope sentence lowers")):
        d = load(f"results/analysis/v2/{f}")
        for col in PRIMARY:
            add(h, f"{text} {col} (pooled)", d, {"model": "pooled", "metric": col}, "lower", "v2", est="difference")
    d = load("results/analysis/v2/h7_friction.csv")
    for col in PRIMARY:
        add("H7", f"friction raises {col} under tight framing (pooled)", d, {"model": "pooled", "metric": col}, "higher", "v2", est="difference")
    d = load("results/analysis/v3/h8_error_type.csv")
    for c in ("D - E1a", "D - E1b"):
        add("H8", f"escalation higher under Permission denied: {c} (pooled)", d, {"model": "pooled", "contrast": c, "metric": "any_escalation"}, "higher", "v3", est="difference")
    d = load("results/analysis/v3/h9_friction_scope.csv")
    for col in ("any_escalation", "any_consequential_oos"):
        add("H9", f"scope sentence lowers {col} under friction (pooled)", d, {"model": "pooled", "contrast": "E2 - D", "metric": col}, "lower", "v3", est="difference")
    d = load("results/analysis/v3/h10_friction_loose.csv")
    for col in PRIMARY:
        add("H10", f"friction raises {col} under loose framing (pooled)", d, {"model": "pooled", "contrast": "E3 - base_loose", "metric": col}, "higher", "v3", est="difference")
    d = load("results/analysis/v3/h11_effort.csv")
    for m in ("claude-sonnet-5-5", "claude-opus-5-5"):
        add("H11", f"effort high changes escalation under friction: {m} (two-sided)", d, {"model": m, "contrast": "E4 - D", "metric": "any_escalation"}, "none", "v3", est="difference")
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", nargs="+", default=["results/scored/v2", "results/scored/v3"])
    ap.add_argument("--out", default="results/analysis/integrated")
    ap.add_argument("--boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261106)
    a = ap.parse_args(argv)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    frames = [pd.read_csv(ROOT / s / "rollouts.csv") for s in a.scored if (ROOT / s / "rollouts.csv").exists()]
    rol = pd.concat(frames).drop_duplicates("rollout_id")
    rol["condition"] = rol.condition.fillna("baseline")
    rol["effort"] = rol.effort.fillna("low") if "effort" in rol else "low"
    rng = np.random.default_rng(a.seed)
    forest(rol, a.boot, rng, out / "fig_int_1_forest.png").to_csv(out / "forest_per_task.csv", index=False)
    (out / "mixed_model.txt").write_text("\n\n".join(mixed(rol, col) for col in PRIMARY))
    table = consolidated()
    table.to_csv(out / "consolidated_table.csv", index=False)
    (out / "consolidated_table.md").write_text("# Consolidated results, H1-H11\n\n" + table.to_markdown(index=False) + "\n")
    print(table[["hypothesis", "verdict", "effect"]].to_string(index=False))


if __name__ == "__main__":
    main()
