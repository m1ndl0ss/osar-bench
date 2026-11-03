# OSAR-bench

Measures how often LLM agents take **out-of-scope actions** on bounded, benign tasks. There is no attacker: the model over-reaches on its own. Every tool call runs inside an in-memory sandbox (files, shell, HTTP, email) and is scored against a pre-registered scope rubric. Each action is labelled in scope, gray or out of scope, and out-of-scope actions get a severity tier: benign, sensitive or consequential.

- Design and hypotheses: [`prereg/PREREGISTRATION.md`](prereg/PREREGISTRATION.md)
- Tasks + rubric: [`prereg/tasks_v1.yaml`](prereg/tasks_v1.yaml) (frozen; `tasks_v0.yaml` is the pilot version)

## Layout

```
osar/sandbox.py   in-memory FS + shell interpreter + mock HTTP/email; emits effects
osar/tools.py     tool schemas (identical for every model)
osar/models.py    Anthropic, OpenAI-compatible (xAI) and scripted adapters
osar/run.py       rollout runner (parallel, resumable, full JSON logs)
osar/rubric.py    deterministic effect labelling + severity
osar/score.py     logs -> effects.csv, rollouts.csv
osar/analyze.py   bootstrap CIs, framing contrasts, cost, figures
osar/plan.py      sample size per cell and budget table from pilot data + spend ledger
osar/kappa.py     blind coding sheet export + Cohen's kappa
osar/pricing.py   list prices used by the spend ledger
tests/            sandbox, shell, rubric, adapter (fake client) and plan tests
```

## Run

```bash
pip install anthropic openai pyyaml pandas matplotlib scikit-learn statsmodels tabulate pytest
python -m pytest -q

# zero-cost dry run (scripted agents with planted over-reach rates 0 / 0.15 / 0.35)
for p in 0.0 0.15 0.35; do python -m osar.run --provider scripted --model scripted-p$p --n 25 --out results/raw/dryrun; done
python -m osar.score   --raw results/raw/dryrun --out results/scored/dryrun
python -m osar.analyze --scored results/scored/dryrun --out results/analysis/dryrun --note " (DRY RUN)"
# sample-size and budget plan on the dry run (scripted models stand in for the tiers; costs are made up)
python -m osar.plan --scored results/scored/dryrun --haiku scripted-p0.15 --sonnet scripted-p0.35 --opus scripted-p0.0 \
  --assume-usd scripted-p0.15=0.005,scripted-p0.35=0.06,scripted-p0.0=0.15

# pilot: Claude Haiku 5.5, 11 tasks x 2 framings x 3 rollouts = 66 rollouts (cents)
export OSAR_ANTHROPIC_KEY=...   # deliberately NOT ANTHROPIC_API_KEY, so Claude Code never picks it up
python -m osar.run --provider anthropic --model claude-haiku-5-5 --n 3 --max-usd 0.50 --out results/raw/pilot

# after the pilot: cost per rollout, n per cell for H2 at 80% power, budget table (reads the spend ledger)
python -m osar.score --raw results/raw/pilot --out results/scored/pilot
python -m osar.plan  --scored results/scored/pilot --ledger results/spend_ledger.jsonl

# confirmatory run (n = 32 per cell, seeds 0-31), then the pre-registered analysis and the coding sheet
python -m osar.run --provider anthropic --model claude-haiku-5-5 --n 32 --max-usd 1.50 --out results/raw/main
python -m osar.score   --raw results/raw/main --out results/scored/main
python -m osar.analyze --scored results/scored/main --out results/analysis/main
python -m osar.kappa export --scored results/scored/main --n 200 --out prereg/coding_sheet.csv

# Grok (run from a machine that can reach api.x.ai)
export XAI_API_KEY=...
python -m osar.run --provider xai --model grok-4.6 --n 32 --out results/raw/main
```

Spend is capped twice: `--max-usd` per invocation and `--global-cap` (default $50) on the all-time ledger `results/spend_ledger.jsonl`. Every model runs at its lowest reasoning setting with thinking on: Claude gets `thinking: {"type": "adaptive"}` + `output_config: {"effort": "low"}`, Grok gets `reasoning_effort: "low"`; `--extra` overrides. If the study key is an organization-level key, set `OSAR_ANTHROPIC_WORKSPACE` to the workspace id (sent as the `anthropic-workspace-id` header).

Pre-registered artifacts are hashed in `prereg/HASHES.txt`; regenerate with

```bash
(cd prereg && sha256sum tasks_v1.yaml tasks_v0.yaml PREREGISTRATION.md ../osar/*.py > HASHES.txt)
```

Every rollout log records:
- the exact model string and API params
- rubric and tool-schema hashes
- the harness git commit
- per-step token usage
- the full trajectory
- the final sandbox state

The runner is resumable: re-running a command skips rollouts that already exist.
