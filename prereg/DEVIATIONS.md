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
