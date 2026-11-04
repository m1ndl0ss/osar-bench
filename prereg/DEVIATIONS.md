# Deviations from the v1 pre-registration

Each entry: date, what changed, why, and whether data had been seen.

## 2026-11-03 — Opus arm interrupted and completed in two parts

- **What.** The Opus arm stopped after 387 of 704 rollouts because the API account's prepaid credit ran out (HTTP 400 "credit balance is too low"); the Haiku and Sonnet arms were already complete. The missing rollouts were run after a top-up with the next unused seeds (32 and up) in each affected cell, as the registration's rule for API failures prescribes.
- **Why.** Billing, not the study's caps (ledger $13.16 of $50 at the interruption).
- **Data seen.** Yes: an interim analysis (`results/analysis/main_interim`, Opus restricted to its six complete tasks) was run and read before the arm was completed. No code, rubric or analysis setting was changed as a result; the confirmatory modules' hashes still match `prereg/HASHES.txt` at tag `prereg-v1`.

## 2026-11-03 — exploratory module added

- **What.** `osar/explore.py` (and its test) added after the freeze. It computes only the exploratory checks listed below and writes `exploratory.md` next to the confirmatory report; it does not feed `osar/analyze.py` or any confirmatory table.
  - consequential out-of-scope rate ignoring `mkdir` on a directory that already existed at the start of the task (a no-op on a real system; the rubric counts it as a state change)
  - out-of-scope rates conditional on completion (already listed as exploratory in §4; reported again here in one place with the framing contrast)
- **Why.** Requested after the interim read of the Opus data showed that its only consequential events under tight framing were no-op `mkdir` calls.
- **Data seen.** Yes. These results are labelled exploratory everywhere they appear.

## 2026-11-03/04 — v2 runs interrupted by the workspace spend limit

- **What.** During the v2 addendum runs the Anthropic workspace's own monthly spend limit ($50) was reached at a ledger total of $50.87, after run A was complete and while B, C and D were in progress (B Opus 526 of 736, C Sonnet 168 of 736, D Haiku 126 of 256; C Opus, D Sonnet and D Opus had not started). Every further request was rejected with HTTP 400 "You have reached your specified API usage limits"; the 1225 rejected requests cost $0.04 and are recorded as errors. The limit was raised to $100 on 2026-11-04 and every incomplete cell was completed with the next unused seeds, as the registration's rule for API failures prescribes. The pre-registered ledger cap of $100 was never reached.
- **Why.** The study's ledger cap had been raised to $100 for v2, but the workspace limit on the provider side was still $50.
- **Data seen.** Run A had been scored and read (per-model rates on the new tasks) before the interruption; the B, C and D data had not been scored. No code, rubric or analysis setting changed as a result.

## 2026-11-04 — modules added after the v3 freeze (descriptive and supplementary only)

- **What.** `osar/integrate.py` (per-task forest plot, mixed-effects logistic model on the shared conditions, consolidated H1–H11 table) and `osar/rater.py` (a model-based second rater for the coding sheet, clearly marked as supplementary and not a substitute for the human kappa) were written while the v3 runs were in progress. Neither changes any confirmatory table; `analyze_v3.py` and `disclose.py` were frozen with the addendum.
- **Why.** Requested with the v3 addendum; written after the freeze to launch the runs in time.
- **Data seen.** v1 and v2 results, yes; no v3 data had been scored when they were written.
