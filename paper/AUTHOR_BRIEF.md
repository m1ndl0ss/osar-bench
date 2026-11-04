# Author brief (private notes, not for publication)

## The study in five sentences

Three Claude 5.5 models (Haiku, Sonnet, Opus) ran 23 short office and ops chores inside an in-memory sandbox with files, a shell, HTTP and email, each under a tight prompt (what to do and where) and a loose one (the goal only). Every effect of every tool call was labelled in scope, gray or out of scope against a rubric frozen before each of four stages, with a severity tier, over 14,720 rollouts and about $155 of API calls. Loose prompts cause a lot of looking around but few unrequested changes; the unrequested changes appear when a loose prompt meets a failing tool. When a privileged command is the only way to finish, the agents mostly stop and say so, and every privileged edit was disclosed, though we cannot tell restraint from distrust of a tool that keeps failing. Changing the error text removed sudo entirely, while an ask-the-user tool, a scope sentence and more reasoning effort changed little.

## Hypotheses in one line each

- H1 (v1, descriptive): every model has a non-zero consequential OOS rate. Supported; 0.9% of all 4,416 baseline rollouts, 1.8% of the v1 ones, mostly Opus on T7.
- H2: loose > tight on any OOS. Supported, +0.475 [0.453, 0.497].
- H2b: loose > tight on consequential OOS. Supported, +0.029 [0.020, 0.039], almost all Opus on T7.
- H3: the three tiers differ on any OOS (two-sided). Opus and Sonnet above Haiku; Opus and Sonnet not different; no monotone claim.
- H4a (v2, new tasks): loose > tight on any OOS. Supported, +0.656.
- H4b: loose > tight on consequential OOS, new tasks. Not supported, +0.002 (floor: the new tasks hardly afford a change).
- H4c: Opus more consequential than the others on the new tasks. Not supported, 0.000 and -0.005.
- H5: an ask-the-user tool lowers OOS. Not supported; used in 3-8% of rollouts.
- H6: a scope sentence lowers OOS. Supported for any OOS (-0.044), not for consequential; completion -0.08.
- H7: one-off friction raises OOS under tight prompts. Supported, +0.277 any, +0.066 consequential (mostly refused attempts, probes and test files; +0.009 for real changes, exploratory).
- H8 (v3): "Permission denied" produces more escalation than two other error texts. Supported, +0.048 each; the other texts produced no sudo at all.
- H9: the scope sentence lowers escalation and consequential OOS under friction. Supported pooled, -0.038 each, all from Sonnet's probes; no effect on real changes (0.000, exploratory); Opus made more real edits with the sentence (7 vs 3).
- H10: friction raises OOS under loose prompts. Supported, +0.070 any, +0.150 consequential, real changes 9-27% vs 1-11%.
- H11: effort high changes escalation under friction (two-sided). Sonnet yes (-0.125, no sudo left), Opus no (+0.008).
- H12 (v4): persistent denial raises privileged edits over one-off denial. Not supported by the registered CI rule: +0.010 [0.000, 0.021], one-sided p = 0.035.
- H13: the scope sentence lowers privileged edits under persistent denial. Supported, -0.013 [-0.023, -0.003], carried by Sonnet (9 rollouts to 1).

## The eight hardest questions, with honest answers

1. **You wrote the rubric yourself. Why should I trust "out of scope"?** Because it was frozen before each stage's data (branches prereg-v1 to prereg-v4, hashes in prereg/HASHES.txt) and because the finer reading is reported too (Table 3, osar/categories.py): the registered consequential metric counts refused attempts and probes, and the paper says what is left when they are removed. The human check is pending; a Sonnet rater agreeing at kappa 0.74 is not a substitute (Limitations, bullet 2).
2. **Your shell is a toy and the models say so. Is "stop and report" restraint or distrust?** We cannot separate them. No rollout used a test or simulation word; one in five F1 rollouts named a sandbox or security policy as the likely cause and every one of those stopped (Section 4.4, exploratory paragraph; Appendix D). Finding (d) is worded as "stopped and reported". The fix is a replication in a container with a real shell and a real sudo (Future Work).
3. **Most of your "sudo" is `sudo -n true`. What is the real escalation rate?** Under one-off denial, 3 rollouts per model for Sonnet and Opus (1.2%), none for Haiku; 28 of Sonnet's 29 probes were followed by a plain retry that worked. Under persistent denial, 1.8% pooled (14 rollouts in F1, 4 in F2), all `sudo sed` on the config file (Sections 4.3 and 4.4, results/analysis/refined/).
4. **H12 has p = 0.035. Why do you call it not supported?** The registered rule (ADDENDUM_v4.md, Section 5) is the pooled one-sided CI excluding zero; the lower bound is exactly 0.000. The test could detect about 1.6 points pooled and saw 1.0. It is a small effect the registered rule does not count, not a null (Section 4.4, Limitations bullet 5).
5. **You say the Opus effect did not replicate. Could it have?** Not well: the twelve v2 tasks are read-only or single-answer chores, so consequential actions were near-impossible by construction (Limitations bullet 6). H4c is "not replicated on tasks that do not afford it". The v1 effect was one task, T7, where Opus emailed colleagues in 7 of 32 loose rollouts.
6. **Three Claude models. What does this say about agents in general?** Only what it says about these three. The title and abstract are qualified in the Limitations; the Grok arm from the v1 plan and an open-weight model are the next runs (Future Work).
7. **Your inter-rater agreement is a model rating a model.** Yes. The 0.74 is a Sonnet rater against the rubric on the v1 coding sheet, clearly labelled model-based; the registered 0.70 threshold is for humans and the human packet (prereg/coding_sheet_v4.csv, 300 items) is ready but not yet rated.
8. **$155 and 32 seeds per cell. Can you detect anything at 1-4% rates?** Barely. At one-sided alpha 0.05 and 80% power, 256 per arm detects about 3.8 points from a 1.2% baseline, 768 pooled about 1.6 points (Limitations bullet 5). The framing and friction effects are 7-66 points and safe; the rare-event contrasts (H4c, H12) are underpowered and reported as such.

## What I would do next with more budget

1. Human raters on the 300-item packet and the 30-case suspicion sheet; publish the kappa.
2. Replicate F1 and F2 in a container with a real shell and sudo, with and without a password prompt.
3. Run Grok 4.6 and one open-weight model through the same four stages.
4. Pre-register the probe/exec and unrequested/collateral categories and the "real change" outcome as primary for the next stage.
5. Add write-tasks to the new-task set so H4b and H4c can fail or succeed honestly.
6. Interleave baselines and arms in time; log the model version string per rollout (already done) and compare.
7. Vary the error text further (ENOSPC, EROFS, a timeout) now that wording is the lever that moves sudo.
