# Supplementary, MODEL-BASED rater (claude-sonnet-5-5), v1 coding sheet

This is not the pre-registered human kappa (placeholder: human raters still to be run). The model saw only the
coding guide, the task prompt and the effect, ten items per call, default sampling (the API no longer accepts temperature).

- Items: 901 (198 ruled by the scorer as in_scope/gray/oos, 703 unclassified shell commands).
- Cohen's kappa, rater vs scorer, on the 198 ruled items: 0.742 (agreement 0.828); the pre-registered threshold for the human kappa is 0.70.
- Over all 901 items (unclassified counted as disagreements by construction): kappa 0.117.
- On the 703 unclassified items the rater said: {'gray': 360, 'in_scope': 305, 'oos': 38}.

Confusion matrix on the ruled items:

|                 |   rater in_scope |   rater gray |   rater oos |
|:----------------|-----------------:|-------------:|------------:|
| scorer in_scope |               58 |            6 |           2 |
| scorer gray     |                9 |           55 |           2 |
| scorer oos      |                3 |           12 |          51 |

Sensitivity analysis with the model rater's oos calls on unclassified items (pre-registered procedure, model-based input): see sensitivity_model_rater.txt.
