# LinkedIn draft

I spent the last few days running a pre-registered study of out-of-scope actions by tool-using LLM agents. The write-up is now on GitHub.

Three Claude 5.5 models (Haiku, Sonnet, Opus) ran 23 small office and ops chores in an in-memory sandbox with files, a shell, HTTP and email. Every effect of every tool call was labelled against a rubric frozen before each stage: 14,720 rollouts, 13 hypotheses, about $154 of API calls.

Four findings:

1. Vague prompts cause a lot of looking around. Dropping the "where" from a request raised the share of rollouts with any out-of-scope action by 48 to 66 points, almost all of it reading and listing, including mail and private notes.
2. Unrequested consequential actions are rare on their own: under 1% of baseline rollouts. An early sign that the largest model emails colleagues did not replicate on new tasks.
3. Vagueness plus a failing tool is where real unrequested changes appear: 9 to 27% of rollouts, depending on the model.
4. When sudo was the only way to finish, 94% of rollouts stopped and told the user. Privileged edits happened in 1.8%, every one disclosed.

The wording of the error message decided whether sudo was tried at all; a clarification tool, a scope sentence and more reasoning effort changed little.

Figure: paper/figures/fig_v4_1_outcomes.png

Code, rubric, logs and paper: https://github.com/m1ndl0ss/osar-bench
