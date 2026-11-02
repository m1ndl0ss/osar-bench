# OSAR-bench

Measures how often LLM agents take **out-of-scope actions** on bounded, benign tasks. There is no attacker: the model over-reaches on its own. Every tool call runs inside an in-memory sandbox (files, shell, HTTP, email) and is scored against a pre-registered scope rubric. Each action is labelled in scope, gray or out of scope, and out-of-scope actions get a severity tier: benign, sensitive or consequential.

- Design and hypotheses: [`prereg/PREREGISTRATION.md`](prereg/PREREGISTRATION.md)
- Tasks + rubric: [`prereg/tasks_v0.yaml`](prereg/tasks_v0.yaml)

## Layout

```
osar/sandbox.py   in-memory FS + shell interpreter + mock HTTP/email; emits effects
osar/tools.py     tool schemas (identical for every model)
osar/models.py    Anthropic, OpenAI-compatible (xAI) and scripted adapters
osar/run.py       rollout runner (parallel, resumable, full JSON logs)
osar/rubric.py    deterministic effect labelling + severity
osar/score.py     logs -> effects.csv, rollouts.csv
osar/analyze.py   bootstrap CIs, framing contrasts, cost, figures
osar/kappa.py     blind coding sheet export + Cohen's kappa
tests/            sandbox/rubric unit tests
```

## Run

```bash
pip install anthropic openai pyyaml pandas matplotlib scikit-learn tabulate pytest
python -m pytest -q

# zero-cost dry run (scripted agents with planted over-reach rates 0 / 0.15 / 0.35)
for p in 0.0 0.15 0.35; do python -m osar.run --provider scripted --model scripted-p$p --n 25 --out results/raw/dryrun; done
python -m osar.score   --raw results/raw/dryrun --out results/scored/dryrun
python -m osar.analyze --scored results/scored/dryrun --out results/analysis/dryrun --note " (DRY RUN)"

# pilot: Claude Haiku 5.5, 11 tasks x 2 framings x 3 rollouts = 66 rollouts (cents)
export OSAR_ANTHROPIC_KEY=...   # deliberately NOT ANTHROPIC_API_KEY, so Claude Code never picks it up
python -m osar.run --provider anthropic --model claude-haiku-5-5 --n 3 --max-usd 0.50 --out results/raw/pilot

# Grok (run from a machine that can reach api.x.ai)
export XAI_API_KEY=...
python -m osar.run --provider xai --model grok-4.6 --n 5 --out results/raw/pilot
```

Every rollout log records:
- the exact model string and API params
- rubric and tool-schema hashes
- the harness git commit
- per-step token usage
- the full trajectory
- the final sandbox state

The runner is resumable: re-running a command skips rollouts that already exist.
