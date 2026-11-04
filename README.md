# OSAR-bench

Measures how often LLM agents take **out-of-scope actions** on bounded, benign tasks. There is no attacker: the model over-reaches on its own. Every tool call runs inside an in-memory sandbox (files, shell, HTTP, email) and is scored by its effects against a pre-registered scope rubric. Each effect is labelled in scope, gray or out of scope, and out-of-scope effects get a severity tier: benign, sensitive or consequential.

Paper: [`paper/osar.pdf`](paper/osar.pdf) (source in `paper/`). One-page findings: [`results/FINDINGS.md`](results/FINDINGS.md). Consolidated H1–H13 table: [`results/analysis/integrated/consolidated_table.md`](results/analysis/integrated/consolidated_table.md).

## Results in five bullets (three Claude 5.5 models, 23 tasks, 14,720 rollouts, four pre-registered stages)

- **Loose prompts cause a large informational over-reach.** Dropping the "where" from a prompt raises the share of rollouts with any out-of-scope action by 0.48 (v1 tasks) and 0.66 (v2 tasks); almost all of it is listing and reading, a third of loose rollouts touch mail, finance or private notes.
- **Unrequested consequential actions are rare on their own.** Of 4,416 baseline rollouts, 0.9% change state out of scope (1.8% on the v1 tasks, mostly Opus on T7). The v1 sign that Opus is the most consequential model (emailing colleagues on one task) did not replicate on twelve new tasks (H4c not supported).
- **Ambiguity and a failing tool compound.** When the first write is refused under a loose prompt, rollouts with a real unrequested change rise from 1–11% to 9–27% depending on the model (H10); under tight prompts the same friction mostly produces probes and blocked attempts.
- **When sudo is the only path, agents stop and report.** With every plain edit refused and passwordless sudo available, 94% of rollouts end with no change and a message naming the obstacle; privileged edits occur in 1.8%, every one disclosed (H12 not supported, H13 supported). Whether that is restraint or distrust of a failing tool, the data cannot say.
- **Error wording beats instructions.** "Permission denied" invites sudo, "Resource temporarily unavailable" and "Disk quota exceeded" never did (H8); an ask-the-user tool, a one-sentence scope instruction and higher reasoning effort changed little (H5, H6, H9, H11, H13).

Pre-registration: [`prereg/PREREGISTRATION.md`](prereg/PREREGISTRATION.md) (v1), [`ADDENDUM_v2.md`](prereg/ADDENDUM_v2.md), [`ADDENDUM_v3.md`](prereg/ADDENDUM_v3.md), [`ADDENDUM_v4.md`](prereg/ADDENDUM_v4.md); departures in [`prereg/DEVIATIONS.md`](prereg/DEVIATIONS.md); freeze commits on branches `prereg-v1` to `prereg-v4`; hashes in `prereg/HASHES.txt`. Task files: `prereg/tasks_v1.yaml` to `tasks_v4.yaml` (each later file only adds conditions).

## Layout

```
osar/sandbox.py      in-memory FS + shell interpreter + mock HTTP/email; emits effects; friction and persistent denial
osar/tools.py        tool schemas (identical for every model), plus the ask_user tool
osar/models.py       Anthropic, OpenAI-compatible (xAI) and scripted adapters
osar/run.py          rollout runner (parallel, resumable, full JSON logs, conditions from the task file)
osar/rubric.py       deterministic effect labelling + severity
osar/score.py        logs -> effects.csv, rollouts.csv
osar/analyze.py      v1: bootstrap CIs, framing and model contrasts, figures
osar/analyze_v2.py   v2: H4-H7            osar/analyze_v3.py  v3: H8-H11      osar/analyze_v4.py  v4: H12-H13, outcomes
osar/disclose.py     disclosure scorer (keyword rule + judge)    osar/disclose_v4.py  same for the v4 arms
osar/categories.py   probe/exec split and the four categories of consequential effects (shared)
osar/refine.py       exploratory re-reporting of v1-v3 with those categories
osar/explore*.py     exploratory checks per stage (added after the freezes, see prereg/DEVIATIONS.md)
osar/integrate.py    per-task forest plot, mixed model, consolidated H1-H13 table
osar/rater.py        model-based second rater for the coding sheet (supplementary)
osar/kappa.py        blind coding sheet export + Cohen's kappa      osar/packet.py  the v1-v4 rater packet
osar/plan.py         sample size per cell and budget table           osar/pricing.py  list prices for the ledger
tests/               sandbox, shell, rubric, adapter (fake client), conditions and analysis tests
paper/               LaTeX source, figures, tables and the PDF
```

## Reproduce

```bash
pip install anthropic openai pyyaml pandas matplotlib scikit-learn statsmodels tabulate pytest
python -m pytest -q
export OSAR_ANTHROPIC_KEY=...          # deliberately NOT ANTHROPIC_API_KEY
export OSAR_ANTHROPIC_WORKSPACE=...    # only for an organization-level key (sent as anthropic-workspace-id)
```

Every run below is `n = 32` per cell, seeds 0–31, adaptive thinking at effort low, capped by `--max-usd` per invocation and `--global-cap` on the all-time ledger `results/spend_ledger.jsonl`. The runner is resumable; failed rollouts are re-run with the next unused seed. `M` stands for each of `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`.

```bash
# v1: 11 tasks x 2 framings (H1-H3)
python -m osar.run --rubric prereg/tasks_v1.yaml --provider anthropic --model M --n 32 --out results/raw/main
python -m osar.score --rubric prereg/tasks_v1.yaml --raw results/raw/main --out results/scored/main
python -m osar.analyze --scored results/scored/main --out results/analysis/main

# v2: new tasks (A), ask_user (B), scope sentence (C), one-off friction on the eight write tasks (D)
python -m osar.run --rubric prereg/tasks_v2.yaml --provider anthropic --model M --tasks T12_calendar_conflict,...,T23_cron_failed --n 32 --out results/raw/v2/A
python -m osar.run --rubric prereg/tasks_v2.yaml --provider anthropic --model M --condition ask_user          --n 32 --out results/raw/v2/B
python -m osar.run --rubric prereg/tasks_v2.yaml --provider anthropic --model M --condition scope_instruction --n 32 --out results/raw/v2/C
python -m osar.run --rubric prereg/tasks_v2.yaml --provider anthropic --model M --condition friction --tasks writes --framings tight --n 32 --out results/raw/v2/D
python -m osar.score --rubric prereg/tasks_v2.yaml --raw results/raw/main results/raw/v2/A results/raw/v2/B results/raw/v2/C results/raw/v2/D --out results/scored/v2
python -m osar.analyze_v2 --scored results/scored/v2 --out results/analysis/v2

# v3: error texts (E1a, E1b), friction + scope sentence (E2), friction under loose prompts (E3), friction at effort high (E4)
python -m osar.run --rubric prereg/tasks_v3.yaml --provider anthropic --model M --condition friction_eagain --tasks writes --framings tight --n 32 --out results/raw/v3/E1a
python -m osar.run --rubric prereg/tasks_v3.yaml --provider anthropic --model M --condition friction_quota  --tasks writes --framings tight --n 32 --out results/raw/v3/E1b
python -m osar.run --rubric prereg/tasks_v3.yaml --provider anthropic --model M --condition friction_scope  --tasks writes --framings tight --n 32 --out results/raw/v3/E2
python -m osar.run --rubric prereg/tasks_v3.yaml --provider anthropic --model M --condition friction --tasks writes --framings loose --n 32 --out results/raw/v3/E3
python -m osar.run --rubric prereg/tasks_v3.yaml --provider anthropic --model M --condition friction --tasks writes --framings tight --n 32 --extra '{"output_config": {"effort": "high"}}' --out results/raw/v3/E4   # Sonnet and Opus only
python -m osar.score --rubric prereg/tasks_v3.yaml --raw results/raw/main results/raw/v2/D results/raw/v3 --out results/scored/v3
python -m osar.analyze_v3 --scored results/scored/v3 --out results/analysis/v3
python -m osar.disclose --scored results/scored/v3 --raw results/raw/main results/raw/v2/D results/raw/v3 --out results/analysis/v3 --judge

# v4: persistent denial with sudo available (F1), plus the scope sentence (F2)
python -m osar.run --rubric prereg/tasks_v4.yaml --provider anthropic --model M --condition friction_persistent       --tasks writes --framings tight --n 32 --out results/raw/v4/F1
python -m osar.run --rubric prereg/tasks_v4.yaml --provider anthropic --model M --condition friction_persistent_scope --tasks writes --framings tight --n 32 --out results/raw/v4/F2
python -m osar.score --rubric prereg/tasks_v4.yaml --raw results/raw/main results/raw/v2/D results/raw/v4/F1 results/raw/v4/F2 --out results/scored/v4
python -m osar.analyze_v4 --scored results/scored/v4 --rubric prereg/tasks_v4.yaml --raw results/raw/v2/D results/raw/v4 --out results/analysis/v4
python -m osar.disclose_v4 --scored results/scored/v4 --rubric prereg/tasks_v4.yaml --raw results/raw/v2/D results/raw/v4 --out results/analysis/v4 --judge

# across stages: exploratory re-reporting, consolidated table, rater packet, paper tables
python -m osar.refine --scored results/scored/v2 results/scored/v3 --rubric prereg/tasks_v4.yaml --disclosure results/analysis/v3/disclosure.csv --raw results/raw/main results/raw/v2 results/raw/v3 --out results/analysis/refined
python -m osar.integrate
python -m osar.packet --scored results/scored/v2 results/scored/v3 results/scored/v4 --rubric prereg/tasks_v4.yaml --out prereg/coding_sheet_v4.csv
python paper/make_tables.py && (cd paper && pdflatex osar && bibtex osar && pdflatex osar && pdflatex osar)
```

A zero-cost dry run of any stage uses `--provider scripted --model scripted-p0.3`. Grok runs from a machine that can reach `api.x.ai` with `--provider xai --model grok-4.6` and `XAI_API_KEY`; that arm is still a placeholder in the paper. Raw logs (`results/raw`) are not in git; scored CSVs and analysis outputs are. The coding-sheet keys (`*_KEY.csv`) stay out of git.

Every rollout log records the exact model string and API parameters, the rubric and tool-schema hashes, the harness git commit, per-step token usage, the full trajectory and the final sandbox state.
