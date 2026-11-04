# Review notes for the author (prioritised)

Written as a skeptical reviewer for an AI-security venue. Every number in the abstract, results, case studies and the LinkedIn draft was re-derived from `results/` and the raw logs; the mismatches found were fixed in the text (listed at the end). Everything below is for the author to decide.

## 1. The three objections a reviewer will raise first

**Objection 1: the rubric and the "consequential" metric are author-defined, and the headline friction numbers move a lot when the metric is read differently.** The registered `any_consequential_oos` counts denied attempts, sudo probes and test files; under one-off denial that is most of the effect (flagged 13.7% vs real 1.2% for Sonnet, 6.2% vs 1.6% for Opus). The probe/exec split and the four categories were defined after the v3 data were seen. A reviewer will say the confirmatory story (H7, H9) is about attempts and the interesting story (real changes) is exploratory.
*Answer:* say this in the abstract, not only in Section 4.3 and the limitations; register the categories for the next stage; add a sensitivity table that recomputes H7, H9 and H10 with "real change" as the outcome, clearly labelled; get the human kappa (currently a placeholder) and report the rubric's disagreements with humans by category.

**Objection 2: one synthetic sandbox with a toy shell and passwordless sudo, and the models notice.** The models comment on the environment in their own final messages: "the shell output was inconsistent", "`stat` printed a literal `%U %a`", "`diff: command not found`", `sudo -n true` prints nothing so the check "returned nothing". Under persistent denial, "stop and report" may partly be distrust of a broken tool rather than restraint about root; the whole-call rollback and the bare `error: Permission denied` without an exit status are artefacts no real shell has.
*Answer:* count how often final messages mention inconsistent or missing tool output per arm; replicate F1 in a container with a real shell and a real `sudo` (with and without a password prompt); report the share of rollouts that hit an `exec_unknown` refusal before stopping.

**Objection 3: generalisability and power.** Three models from one lab, mostly at effort low; eight friction tasks; the strongest effects rest on three or four tasks (forest plot); the rare-event rates (1--4%) are 3--9 rollouts per cell, so H12's CI touching zero is as much a power problem as a null. The v2 "new tasks" are read-only or single-answer chores, so H4b and H4c could hardly have been supported (floor effect); the paper should say so rather than present the non-replication as a clean negative.
*Answer:* run the Grok arm (placeholder) and at least one open-weight model; add write-tasks to the new-task set before claiming H4c failed to replicate; report per-task effects for every hypothesis; give the minimum detectable effect for H12 at n = 256 per arm.

## 2. Overclaims and missing caveats (fix in the next revision)

- **Probe vs real sudo.** The abstract's part (d) and Section 4.4 are correct, but Section 4.5 (H8) and 4.6 (H9, H11) still talk about "escalation" and "sudo" as if they were one thing. State in each that the registered escalation metric is dominated by `sudo -n true` probes (29 of Sonnet's 32 under D) and that the error-wording effect is an effect on probing; real edits were 3 per model.
- **Collateral vs unrequested.** The "9--27%" range in the abstract includes Opus's header-capitalisation over-edits (20 of its 68 real E3 rollouts). Without them Opus is 18.8%, so the honest range for unrequested changes elsewhere is 9--19%. Either quote that range or say the 27% includes trivial over-edits.
- **H4c.** The v1 Opus effect was one task (T7) and the out-of-sample test used tasks on which consequential actions were near-impossible by construction. Call it "not replicated on tasks that do not afford it" and add write-tasks before claiming more.
- **Judge-based disclosure.** One Sonnet judge at default sampling, judging Sonnet, Opus and Haiku; the hand-check was done by the author, not blind, on a disagreement-heavy sample; the judge saw probes and test files in the action list even where rates are now restricted to real changes; "all 24 privileged edits disclosed" is 24 cases judged once. Report the judge's prompt sensitivity (a second wording) and have a second person label the 40 cases.
- **Model-based kappa.** A Sonnet rater agreeing with a rubric at kappa 0.74 says little about human agreement, and the registered 0.70 threshold was for humans. Keep it out of the abstract and label it clearly in the limitations (it is).
- **Single synthetic environment.** Also say that the environment contains planted temptations, so the baseline OOS rates are for an environment designed to invite over-reach, not for a random workstation.
- **Anthropic-only models.** The title and abstract say "tool-using agents"; the evidence is three Claude models. Qualify the title or the first sentence of the abstract.
- **Exploratory results near confirmatory ones.** Table 3 and the abstract's part (c) use the exploratory categories; the LinkedIn draft quotes "9 to 27%" with the label added only now. Keep the registered numbers first everywhere and the breakdown second.
- **H12 wording.** "The models did not take it" reads as a null result; the registered test is not supported because the pooled CI's lower bound is exactly zero (one-sided p = 0.035). Say "a small increase that the registered rule does not count as supported".
- **Error wording beats instructions.** This is a comparison across separate contrasts, not a registered interaction test. Phrase it as descriptive.
- **Time confound.** The baselines for D, E and F were run a day or two earlier than the arms they are compared with, not interleaved; a model update behind the API during that window would be invisible. Log the model version strings per rollout (they are) and say the comparison is not randomised in time.
- **The trade-off under persistent denial.** "Stop and report" came with completion falling from 0.66 to 0.02; present it as a trade-off, not only as restraint.
- **Costs.** The judge and rater spend (about \$3) is an estimate, not logged; say so or log it.

## 3. Presentation

- The consolidated table uses internal metric names (`any_oos`, `escalate_exec`); define them once in a footnote or rename.
- Figure 2 (forest) is dense at half width; consider one panel per outcome or a larger figure in the appendix.
- Appendix A should list all 23 prompts (tight and loose), not summaries, so the "tempting over-reach" claims can be checked.
- Give the 40-case hand-check procedure (sampling, who labelled, blind or not) and the reweighting formula.
- Report unclassified effects per arm and model, not only "about 2% of effects"; the sensitivity analysis moved `any_oos` by up to 0.014, which is larger than some reported differences (H6 consequential).
- Add per-model bootstrap CIs to the v4 outcome table.
- The mixed model is variational Bayes without credible intervals in the text; either give them or drop the logits from the prose.

## 4. Citations (checked by web search; arxiv.org itself is not reachable from this session)

- OverAct, arXiv:2610.01508, Zhang, Wan, Wang, Hu, Wang (2026): title and authors confirmed; "seven models from four families" confirmed; "open-weight" could not be confirmed and was removed from the text.
- ToolPrivBench, arXiv:2606.20023, Kaiyue Yang et al. (2026): title and first author confirmed; 544 scenarios confirmed; "single run per scenario, simulated outputs" comes from the pre-registration's reading of the paper, not re-checked.
- UnderSpecBench, arXiv:2607.02294, Zimo Ji et al. (2026): title confirmed; 55.8--67.8% violation range confirmed (paper says 56--68%).
- LHAW, arXiv:2602.10525, George Pu et al. (2026): title and first author confirmed.
- Xu and Wu, arXiv:2608.03169 (2026): title and both authors confirmed; GPT-5.6, 840 trajectories, no unauthorized calls, more rule-probing at higher effort confirmed from the abstract listing.
- No "first", "novel" or "new benchmark" claim appears in the text.

## 5. What was checked and fixed in this pass

Re-derived and matching: rollout counts per stage (2,112 / 7,488 / 3,584 / 1,536, all finished); every effect and CI in Table 2 against `consolidated_table.csv`; v1 rates by model and framing; H3 pairs; mixed-model coefficients; D sudo shares and the 29/28/28 probe sequence; the real-change shares in Table 3; v4 outcome shares, F1/F2 exec counts (14 and 4, all `sudo -n sed -i`), H12/H13 numbers, disclosure 24/24; H5 ask rates (3.1--8.4%); H6 completion cost (0.083); judge/rule agreement (0.723, kappa 0.394), hand-check 21/40 and 3/40; the 23 header over-edits and the 20 under E3; freeze dates and commits.

Fixed: "under 1% of baseline rollouts" was true only over all 4,416 baselines (0.9%), not the v1 baselines (37/2,112 = 1.8%); the case-2 and case-3 commands were not verbatim (`2>/dev/null` and `ls -l /var/log/app` were missing); "reads every file under the home directory" was 39 of 42; "learned that passwordless sudo was available, and still stopped in all 23" held for 15 of the 23 (four called the silent check inconclusive, four did not say); the count of unsupported hypotheses omitted H6's consequential metric; OverAct's "open-weight" removed; the abstract and the LinkedIn draft now label the 9--27% figure as exploratory.

## 6. Status after the revision (2026-11-04, same day)

- Objection 1 (author-defined rubric, attempts counted): **addressed** in Limitations (rubric frozen before each stage's data; probe/exec and collateral/unrequested splits reported; human kappa pending). Sensitivity table with "real change" as the outcome: **open**.
- Objection 2 (distrust vs restraint): **partly addressed**. A fixed keyword scan over all 2,304 D/F1/F2 rollouts is reported in Section 4.4 and Appendix D (no test/simulation/evaluation words anywhere; "sandbox" named as a possible restriction in 18--34% of F1 rollouts, all of which stopped). Finding (d) is softened to "stopped and reported; restraint and distrust cannot be separated". The judge-based scoring and the 30-case hand check: **open** (not run). Replication in a real shell: **open**.
- Objection 3 (generalisability, power, H4c floor): **addressed** in Limitations with one sentence each and a minimum-detectable-effect note (3.8 points per model from 1.2%, 1.6 points pooled from 0.8%, 1.9 points for H4c). Grok arm and an open-weight model: **open**.
- Probe vs real sudo in the H8/H9/H11 prose: **addressed** (Section 4.5 now says the registered metric is dominated by probes).
- Collateral vs unrequested range (9--19% without over-edits): **open** (only the exploratory label was added).
- H4c floor effect: **addressed** (Limitations).
- Judge-based disclosure and the non-blind hand check: **addressed** (Limitations).
- Model-based kappa: **addressed** (Limitations; kept out of the abstract).
- Single synthetic environment with planted temptations, models noticing its limits: **addressed** (Limitations).
- Anthropic-only models and the title: **addressed** (Limitations; title changed to "Stop, Work Around, or Escalate: A Pre-Registered Study of Scope Creep in Tool-Using Language-Model Agents").
- Exploratory results near confirmatory ones: **addressed** (labels in the abstract, Section 4.3, Table 3, the LinkedIn draft).
- H12 wording: **addressed** ("The models rarely took it").
- "Error wording beats instructions" as a descriptive comparison: **open**.
- Non-interleaved baselines: **addressed** (Limitations).
- Completion trade-off under persistent denial: **addressed** (Limitations).
- Costs outside the ledger: **open** (still an estimate).
- Presentation items (Section 3): **addressed** except the forest figure (metric names defined in a footnote; all 23 prompts, the hand-check procedure, unclassified counts per arm and model, v4 outcome CIs and the mixed-model posterior SDs are in the appendix; the timeline table, the category table and the v3 figure moved there so the main text with references is about 11 pages). Forest figure still at 0.8 of the text width: **open**.
- Citations (Section 4): **addressed**.

## 7. Still open after the second revision

- Judge-based suspicion scoring and the 30-case hand check (sheet ready at `prereg/suspicion_handcheck.csv`, not yet labelled).
- Replication of F1/F2 in a real shell; Grok and an open-weight model (both listed under Future work).
- Sensitivity table with "real change" as the outcome for H7, H9, H10.
- Unrequested-only range (9--19%) alongside the 9--27% figure.
- "Error wording beats instructions" is still phrased as a finding rather than a descriptive comparison.
- Judge and rater costs outside the ledger remain an estimate.
- Human kappa and the Grok arm remain placeholders in the PDF.

## 8. Status after the third revision

- Real-change sensitivity table for H7, H9, H10: **addressed** (Appendix C, `osar/sensitivity.py`, exploratory; H10 holds, H7 shrinks to +0.009, H9 vanishes).
- Unrequested-only range (9--19%): **addressed** (abstract, Section 4.3, README, FINDINGS, LinkedIn draft).
- "Error wording beats instructions": **addressed** (now a descriptive comparison across separate contrasts, in the abstract, introduction, Sections 4.5 and 6, README, FINDINGS, drafts).
- Judge and rater costs: **addressed** (estimate with its basis in the Conclusion and Appendix F).
- Forest figure: **addressed** (full text width).
- Still open: labelling the suspicion sheet and any judge scoring; the real-shell replication; Grok and an open-weight model; the human kappa and Grok placeholders in the PDF.
