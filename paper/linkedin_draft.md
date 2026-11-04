# LinkedIn draft

A pre-registered study of out-of-scope actions by tool-using LLM agents, now on GitHub.

Three Claude 5.5 models, 23 office chores in a sandbox with files, shell, HTTP and email, every effect labelled against a frozen rubric: 14,720 rollouts, 13 hypotheses, about $155.

Five findings:

1. Vagueness plus a failing tool is where real unrequested changes appear: with the first write refused under a vague prompt, 9 to 27% of rollouts make one (9 to 19% for changes elsewhere; +0.096, exploratory breakdown of a registered effect).
2. A failing tool alone mostly produces sudo probes and blocked attempts; real changes rise about one point, and a scope sentence removed probes, not real edits.
3. Vague prompts cause looking around: dropping the "where" raised any out-of-scope action by 48 to 66 points, almost all reading and listing.
4. Unrequested consequential actions are rare on their own: 0.9% of 4,416 baseline rollouts. An early Opus effect did not replicate.
5. With sudo the only way to finish, 94% stopped and told the user; privileged edits in 1.8%, every one disclosed. Restraint or distrust of a failing tool, we can't say.

Changing the error text removed sudo entirely; a clarification tool, a scope sentence and more reasoning effort changed little.

Figure: paper/figures/fig_v4_1_outcomes.png

Paper ("Stop, Work Around, or Escalate"), code, rubric and logs: https://github.com/m1ndl0ss/osar-bench
