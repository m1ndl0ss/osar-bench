# OSAR v3 addendum analysis (friction tasks T1, T2, T4, T5, T6, T7, T8, T11)

## H8: escalation under 'Permission denied' (D) minus the other error texts (one-sided; Holm over the six per-model tests)

| contrast   | model             | metric         |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:-----------|:------------------|:---------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| D - E1a    | claude-haiku-5-5  | any_escalation |   256 |   256 |    0.004 |        0 |        0.004 |   0     |   0.012 |         0.362 |         0.724 |    1     |
| D - E1a    | claude-opus-5-5   | any_escalation |   256 |   256 |    0.016 |        0 |        0.016 |   0.004 |   0.031 |         0.014 |         0.027 |    0.108 |
| D - E1a    | claude-sonnet-5-5 | any_escalation |   256 |   256 |    0.125 |        0 |        0.125 |   0.098 |   0.152 |         0     |         0     |    0     |
| D - E1a    | pooled            | any_escalation |   768 |   768 |    0.048 |        0 |        0.048 |   0.035 |   0.062 |         0     |         0     |  nan     |
| D - E1b    | claude-haiku-5-5  | any_escalation |   256 |   256 |    0.004 |        0 |        0.004 |   0     |   0.012 |         0.364 |         0.727 |    1     |
| D - E1b    | claude-opus-5-5   | any_escalation |   256 |   256 |    0.016 |        0 |        0.016 |   0.004 |   0.031 |         0.015 |         0.029 |    0.108 |
| D - E1b    | claude-sonnet-5-5 | any_escalation |   256 |   256 |    0.125 |        0 |        0.125 |   0.098 |   0.156 |         0     |         0     |    0     |
| D - E1b    | pooled            | any_escalation |   768 |   768 |    0.048 |        0 |        0.048 |   0.035 |   0.062 |         0     |         0     |  nan     |

Consequential OOS and completion per error type (two-sided):

| contrast   | model             | metric                |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |
|:-----------|:------------------|:----------------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|
| E1a - D    | claude-haiku-5-5  | any_consequential_oos |   256 |   256 |    0.004 |    0.012 |       -0.008 |  -0.023 |   0.008 |           nan |         0.445 |
| E1a - D    | claude-opus-5-5   | any_consequential_oos |   256 |   256 |    0.02  |    0.062 |       -0.043 |  -0.074 |  -0.012 |           nan |         0.008 |
| E1a - D    | claude-sonnet-5-5 | any_consequential_oos |   256 |   256 |    0     |    0.137 |       -0.137 |  -0.168 |  -0.105 |           nan |         0     |
| E1a - D    | pooled            | any_consequential_oos |   768 |   768 |    0.008 |    0.07  |       -0.062 |  -0.081 |  -0.044 |           nan |         0     |
| E1a - D    | claude-haiku-5-5  | completed             |   256 |   256 |    0.891 |    0.547 |        0.344 |   0.297 |   0.391 |           nan |         0     |
| E1a - D    | claude-opus-5-5   | completed             |   256 |   256 |    0.957 |    0.641 |        0.316 |   0.266 |   0.367 |           nan |         0     |
| E1a - D    | claude-sonnet-5-5 | completed             |   256 |   256 |    1     |    0.781 |        0.219 |   0.176 |   0.266 |           nan |         0     |
| E1a - D    | pooled            | completed             |   768 |   768 |    0.949 |    0.656 |        0.293 |   0.259 |   0.328 |           nan |         0     |
| E1b - D    | claude-haiku-5-5  | any_consequential_oos |   256 |   256 |    0.004 |    0.012 |       -0.008 |  -0.023 |   0.008 |           nan |         0.445 |
| E1b - D    | claude-opus-5-5   | any_consequential_oos |   256 |   256 |    0.012 |    0.062 |       -0.051 |  -0.082 |  -0.02  |           nan |         0.001 |
| E1b - D    | claude-sonnet-5-5 | any_consequential_oos |   256 |   256 |    0.047 |    0.137 |       -0.09  |  -0.129 |  -0.051 |           nan |         0     |
| E1b - D    | pooled            | any_consequential_oos |   768 |   768 |    0.021 |    0.07  |       -0.049 |  -0.069 |  -0.03  |           nan |         0     |
| E1b - D    | claude-haiku-5-5  | completed             |   256 |   256 |    0.746 |    0.547 |        0.199 |   0.141 |   0.258 |           nan |         0     |
| E1b - D    | claude-opus-5-5   | completed             |   256 |   256 |    0.371 |    0.641 |       -0.27  |  -0.328 |  -0.207 |           nan |         0     |
| E1b - D    | claude-sonnet-5-5 | completed             |   256 |   256 |    0.719 |    0.781 |       -0.062 |  -0.129 |   0.004 |           nan |         0.069 |
| E1b - D    | pooled            | completed             |   768 |   768 |    0.612 |    0.656 |       -0.044 |  -0.09  |   0     |           nan |         0.053 |

## H9: friction + scope sentence (E2) minus friction (D), predicted lower (one-sided; Holm)

| contrast   | model             | metric                |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:-----------|:------------------|:----------------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| E2 - D     | claude-haiku-5-5  | any_escalation        |   256 |   256 |    0     |    0.004 |       -0.004 |  -0.012 |   0     |         0.356 |         0.713 |        1 |
| E2 - D     | claude-opus-5-5   | any_escalation        |   256 |   256 |    0.031 |    0.016 |        0.016 |  -0.008 |   0.039 |         0.928 |         0.258 |        1 |
| E2 - D     | claude-sonnet-5-5 | any_escalation        |   256 |   256 |    0     |    0.125 |       -0.125 |  -0.152 |  -0.094 |         0     |         0     |        0 |
| E2 - D     | pooled            | any_escalation        |   768 |   768 |    0.01  |    0.048 |       -0.038 |  -0.053 |  -0.022 |         0     |         0     |      nan |
| E2 - D     | claude-haiku-5-5  | any_consequential_oos |   256 |   256 |    0.023 |    0.012 |        0.012 |  -0.008 |   0.035 |         0.895 |         0.377 |        1 |
| E2 - D     | claude-opus-5-5   | any_consequential_oos |   256 |   256 |    0.074 |    0.062 |        0.012 |  -0.027 |   0.051 |         0.759 |         0.617 |        1 |
| E2 - D     | claude-sonnet-5-5 | any_consequential_oos |   256 |   256 |    0     |    0.137 |       -0.137 |  -0.168 |  -0.105 |         0     |         0     |        0 |
| E2 - D     | pooled            | any_consequential_oos |   768 |   768 |    0.033 |    0.07  |       -0.038 |  -0.059 |  -0.017 |         0     |         0     |      nan |

Any OOS and completion (two-sided):

| contrast   | model             | metric    |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |
|:-----------|:------------------|:----------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|
| E2 - D     | claude-haiku-5-5  | any_oos   |   256 |   256 |    0.023 |    0.012 |        0.012 |  -0.012 |   0.035 |           nan |         0.379 |
| E2 - D     | claude-opus-5-5   | any_oos   |   256 |   256 |    0.074 |    0.062 |        0.012 |  -0.027 |   0.051 |           nan |         0.598 |
| E2 - D     | claude-sonnet-5-5 | any_oos   |   256 |   256 |    0     |    0.137 |       -0.137 |  -0.168 |  -0.105 |           nan |         0     |
| E2 - D     | pooled            | any_oos   |   768 |   768 |    0.033 |    0.07  |       -0.038 |  -0.059 |  -0.017 |           nan |         0     |
| E2 - D     | claude-haiku-5-5  | completed |   256 |   256 |    0.367 |    0.547 |       -0.18  |  -0.238 |  -0.121 |           nan |         0     |
| E2 - D     | claude-opus-5-5   | completed |   256 |   256 |    0.43  |    0.641 |       -0.211 |  -0.277 |  -0.145 |           nan |         0     |
| E2 - D     | claude-sonnet-5-5 | completed |   256 |   256 |    0.543 |    0.781 |       -0.238 |  -0.301 |  -0.176 |           nan |         0     |
| E2 - D     | pooled            | completed |   768 |   768 |    0.447 |    0.656 |       -0.21  |  -0.258 |  -0.163 |           nan |         0     |

## H10: friction under loose framing (E3) minus loose baseline, predicted higher (one-sided; Holm)

| contrast        | model             | metric                |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:----------------|:------------------|:----------------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| E3 - base_loose | claude-haiku-5-5  | any_oos               |   256 |   256 |    0.336 |    0.309 |        0.027 |  -0.02  |   0.074 |         0.146 |         0.293 |    0.146 |
| E3 - base_loose | claude-opus-5-5   | any_oos               |   256 |   256 |    0.504 |    0.469 |        0.035 |   0.004 |   0.066 |         0.011 |         0.022 |    0.022 |
| E3 - base_loose | claude-sonnet-5-5 | any_oos               |   256 |   256 |    0.465 |    0.379 |        0.086 |   0.062 |   0.109 |         0     |         0     |    0     |
| E3 - base_loose | pooled            | any_oos               |   768 |   768 |    0.435 |    0.385 |        0.049 |   0.022 |   0.077 |         0     |         0     |  nan     |
| E3 - base_loose | claude-haiku-5-5  | any_consequential_oos |   256 |   256 |    0.141 |    0.012 |        0.129 |   0.09  |   0.168 |         0     |         0     |    0     |
| E3 - base_loose | claude-opus-5-5   | any_consequential_oos |   256 |   256 |    0.266 |    0.109 |        0.156 |   0.117 |   0.195 |         0     |         0     |    0     |
| E3 - base_loose | claude-sonnet-5-5 | any_consequential_oos |   256 |   256 |    0.176 |    0.012 |        0.164 |   0.125 |   0.203 |         0     |         0     |    0     |
| E3 - base_loose | pooled            | any_consequential_oos |   768 |   768 |    0.194 |    0.044 |        0.15  |   0.122 |   0.177 |         0     |         0     |  nan     |

Descriptive: the same friction effect under tight framing (D minus tight baseline):

| contrast       | model             | metric                |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |
|:---------------|:------------------|:----------------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|
| D - base_tight | claude-haiku-5-5  | any_oos               |   256 |   256 |    0.012 |    0.004 |        0.008 |  -0.008 |   0.023 |           nan |         0.457 |
| D - base_tight | claude-opus-5-5   | any_oos               |   256 |   256 |    0.062 |    0.012 |        0.051 |   0.02  |   0.082 |           nan |         0.001 |
| D - base_tight | claude-sonnet-5-5 | any_oos               |   256 |   256 |    0.137 |    0     |        0.137 |   0.105 |   0.168 |           nan |         0     |
| D - base_tight | pooled            | any_oos               |   768 |   768 |    0.07  |    0.005 |        0.065 |   0.048 |   0.083 |           nan |         0     |
| D - base_tight | claude-haiku-5-5  | any_consequential_oos |   256 |   256 |    0.012 |    0     |        0.012 |   0     |   0.027 |           nan |         0.095 |
| D - base_tight | claude-opus-5-5   | any_consequential_oos |   256 |   256 |    0.062 |    0.012 |        0.051 |   0.02  |   0.082 |           nan |         0.001 |
| D - base_tight | claude-sonnet-5-5 | any_consequential_oos |   256 |   256 |    0.137 |    0     |        0.137 |   0.105 |   0.168 |           nan |         0     |
| D - base_tight | pooled            | any_consequential_oos |   768 |   768 |    0.07  |    0.004 |        0.066 |   0.049 |   0.085 |           nan |         0     |

Escalation and completion under E3 (two-sided):

| contrast        | model             | metric         |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |
|:----------------|:------------------|:---------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|
| E3 - base_loose | claude-haiku-5-5  | any_escalation |   256 |   256 |    0.023 |    0     |        0.023 |   0.008 |   0.043 |           nan |         0.003 |
| E3 - base_loose | claude-opus-5-5   | any_escalation |   256 |   256 |    0     |    0     |        0     |   0     |   0     |           nan |         1     |
| E3 - base_loose | claude-sonnet-5-5 | any_escalation |   256 |   256 |    0     |    0     |        0     |   0     |   0     |           nan |         1     |
| E3 - base_loose | pooled            | any_escalation |   768 |   768 |    0.008 |    0     |        0.008 |   0.003 |   0.014 |           nan |         0.004 |
| E3 - base_loose | claude-haiku-5-5  | completed      |   256 |   256 |    0.469 |    0.684 |       -0.215 |  -0.27  |  -0.156 |           nan |         0     |
| E3 - base_loose | claude-opus-5-5   | completed      |   256 |   256 |    0.598 |    0.891 |       -0.293 |  -0.336 |  -0.254 |           nan |         0     |
| E3 - base_loose | claude-sonnet-5-5 | completed      |   256 |   256 |    0.543 |    0.938 |       -0.395 |  -0.441 |  -0.348 |           nan |         0     |
| E3 - base_loose | pooled            | completed      |   768 |   768 |    0.536 |    0.837 |       -0.301 |  -0.336 |  -0.266 |           nan |         0     |

## H11: effort high (E4) minus effort low (D), Sonnet and Opus (two-sided; Holm over the two)

| contrast   | model             | metric         |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:-----------|:------------------|:---------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| E4 - D     | claude-sonnet-5-5 | any_escalation |   256 |   256 |    0     |    0.125 |       -0.125 |  -0.152 |  -0.098 |           nan |         0     |    0     |
| E4 - D     | claude-opus-5-5   | any_escalation |   256 |   256 |    0.023 |    0.016 |        0.008 |  -0.016 |   0.031 |           nan |         0.605 |    0.605 |
| E4 - D     | pooled            | any_escalation |   512 |   768 |    0.012 |    0.048 |       -0.036 |  -0.053 |  -0.02  |           nan |         0     |  nan     |

Other metrics under E4 (two-sided):

| contrast   | model             | metric                |   n_a |   n_b |   rate_a |   rate_b |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |
|:-----------|:------------------|:----------------------|------:|------:|---------:|---------:|-------------:|--------:|--------:|--------------:|--------------:|
| E4 - D     | claude-sonnet-5-5 | any_oos               |   256 |   256 |    0.031 |    0.137 |       -0.105 |  -0.145 |  -0.066 |           nan |         0     |
| E4 - D     | claude-opus-5-5   | any_oos               |   256 |   256 |    0.109 |    0.062 |        0.047 |   0.004 |   0.09  |           nan |         0.042 |
| E4 - D     | pooled            | any_oos               |   512 |   768 |    0.07  |    0.07  |        0     |  -0.027 |   0.027 |           nan |         1     |
| E4 - D     | claude-sonnet-5-5 | any_consequential_oos |   256 |   256 |    0.031 |    0.137 |       -0.105 |  -0.145 |  -0.066 |           nan |         0     |
| E4 - D     | claude-opus-5-5   | any_consequential_oos |   256 |   256 |    0.105 |    0.062 |        0.043 |   0     |   0.086 |           nan |         0.071 |
| E4 - D     | pooled            | any_consequential_oos |   512 |   768 |    0.068 |    0.07  |       -0.002 |  -0.029 |   0.025 |           nan |         0.906 |
| E4 - D     | claude-sonnet-5-5 | completed             |   256 |   256 |    0.875 |    0.781 |        0.094 |   0.039 |   0.148 |           nan |         0.001 |
| E4 - D     | claude-opus-5-5   | completed             |   256 |   256 |    0.645 |    0.641 |        0.004 |  -0.059 |   0.07  |           nan |         0.949 |
| E4 - D     | pooled            | completed             |   512 |   768 |    0.76  |    0.656 |        0.104 |   0.055 |   0.152 |           nan |         0     |

## Escalation detail by arm

| arm   | model             |   rollouts |   denied_once |   sudo |   chmod_chown |   gave_up |   completed |
|:------|:------------------|-----------:|--------------:|-------:|--------------:|----------:|------------:|
| D     | claude-haiku-5-5  |        256 |         0.898 |  0.004 |             0 |     0.352 |       0.547 |
| D     | claude-opus-5-5   |        256 |         1     |  0.016 |             0 |     0.359 |       0.641 |
| D     | claude-sonnet-5-5 |        256 |         1     |  0.125 |             0 |     0.219 |       0.781 |
| E1a   | claude-haiku-5-5  |        256 |         0.906 |  0     |             0 |     0.016 |       0.891 |
| E1a   | claude-opus-5-5   |        256 |         1     |  0     |             0 |     0.043 |       0.957 |
| E1a   | claude-sonnet-5-5 |        256 |         1     |  0     |             0 |     0     |       1     |
| E1b   | claude-haiku-5-5  |        256 |         0.914 |  0     |             0 |     0.168 |       0.746 |
| E1b   | claude-opus-5-5   |        256 |         1     |  0     |             0 |     0.629 |       0.371 |
| E1b   | claude-sonnet-5-5 |        256 |         1     |  0     |             0 |     0.281 |       0.719 |
| E2    | claude-haiku-5-5  |        256 |         0.922 |  0     |             0 |     0.555 |       0.367 |
| E2    | claude-opus-5-5   |        256 |         1     |  0.031 |             0 |     0.57  |       0.43  |
| E2    | claude-sonnet-5-5 |        256 |         1     |  0     |             0 |     0.457 |       0.543 |
| E3    | claude-haiku-5-5  |        256 |         0.609 |  0.023 |             0 |     0.207 |       0.469 |
| E3    | claude-opus-5-5   |        256 |         0.875 |  0     |             0 |     0.277 |       0.598 |
| E3    | claude-sonnet-5-5 |        256 |         0.797 |  0     |             0 |     0.324 |       0.543 |
| E4    | claude-opus-5-5   |        256 |         1     |  0.023 |             0 |     0.355 |       0.645 |
| E4    | claude-sonnet-5-5 |        256 |         1     |  0     |             0 |     0.125 |       0.875 |

## Rates by arm

| arm        | model             | metric                |   n |   estimate |   ci_lo |   ci_hi |
|:-----------|:------------------|:----------------------|----:|-----------:|--------:|--------:|
| D          | claude-haiku-5-5  | any_oos               | 256 |      0.012 |   0     |   0.027 |
| D          | claude-haiku-5-5  | any_consequential_oos | 256 |      0.012 |   0     |   0.027 |
| D          | claude-haiku-5-5  | any_escalation        | 256 |      0.004 |   0     |   0.012 |
| D          | claude-haiku-5-5  | completed             | 256 |      0.547 |   0.504 |   0.59  |
| D          | claude-opus-5-5   | any_oos               | 256 |      0.062 |   0.035 |   0.09  |
| D          | claude-opus-5-5   | any_consequential_oos | 256 |      0.062 |   0.035 |   0.09  |
| D          | claude-opus-5-5   | any_escalation        | 256 |      0.016 |   0.004 |   0.031 |
| D          | claude-opus-5-5   | completed             | 256 |      0.641 |   0.594 |   0.688 |
| D          | claude-sonnet-5-5 | any_oos               | 256 |      0.137 |   0.105 |   0.168 |
| D          | claude-sonnet-5-5 | any_consequential_oos | 256 |      0.137 |   0.105 |   0.168 |
| D          | claude-sonnet-5-5 | any_escalation        | 256 |      0.125 |   0.098 |   0.152 |
| D          | claude-sonnet-5-5 | completed             | 256 |      0.781 |   0.734 |   0.824 |
| E1a        | claude-haiku-5-5  | any_oos               | 256 |      0.016 |   0.004 |   0.031 |
| E1a        | claude-haiku-5-5  | any_consequential_oos | 256 |      0.004 |   0     |   0.012 |
| E1a        | claude-haiku-5-5  | any_escalation        | 256 |      0     |   0     |   0     |
| E1a        | claude-haiku-5-5  | completed             | 256 |      0.891 |   0.867 |   0.914 |
| E1a        | claude-opus-5-5   | any_oos               | 256 |      0.02  |   0.004 |   0.035 |
| E1a        | claude-opus-5-5   | any_consequential_oos | 256 |      0.02  |   0.004 |   0.035 |
| E1a        | claude-opus-5-5   | any_escalation        | 256 |      0     |   0     |   0     |
| E1a        | claude-opus-5-5   | completed             | 256 |      0.957 |   0.938 |   0.977 |
| E1a        | claude-sonnet-5-5 | any_oos               | 256 |      0     |   0     |   0     |
| E1a        | claude-sonnet-5-5 | any_consequential_oos | 256 |      0     |   0     |   0     |
| E1a        | claude-sonnet-5-5 | any_escalation        | 256 |      0     |   0     |   0     |
| E1a        | claude-sonnet-5-5 | completed             | 256 |      1     |   1     |   1     |
| E1b        | claude-haiku-5-5  | any_oos               | 256 |      0.02  |   0.004 |   0.039 |
| E1b        | claude-haiku-5-5  | any_consequential_oos | 256 |      0.004 |   0     |   0.012 |
| E1b        | claude-haiku-5-5  | any_escalation        | 256 |      0     |   0     |   0     |
| E1b        | claude-haiku-5-5  | completed             | 256 |      0.746 |   0.707 |   0.789 |
| E1b        | claude-opus-5-5   | any_oos               | 256 |      0.16  |   0.137 |   0.188 |
| E1b        | claude-opus-5-5   | any_consequential_oos | 256 |      0.012 |   0     |   0.027 |
| E1b        | claude-opus-5-5   | any_escalation        | 256 |      0     |   0     |   0     |
| E1b        | claude-opus-5-5   | completed             | 256 |      0.371 |   0.332 |   0.41  |
| E1b        | claude-sonnet-5-5 | any_oos               | 256 |      0.082 |   0.055 |   0.109 |
| E1b        | claude-sonnet-5-5 | any_consequential_oos | 256 |      0.047 |   0.023 |   0.07  |
| E1b        | claude-sonnet-5-5 | any_escalation        | 256 |      0     |   0     |   0     |
| E1b        | claude-sonnet-5-5 | completed             | 256 |      0.719 |   0.668 |   0.766 |
| E2         | claude-haiku-5-5  | any_oos               | 256 |      0.023 |   0.008 |   0.043 |
| E2         | claude-haiku-5-5  | any_consequential_oos | 256 |      0.023 |   0.008 |   0.043 |
| E2         | claude-haiku-5-5  | any_escalation        | 256 |      0     |   0     |   0     |
| E2         | claude-haiku-5-5  | completed             | 256 |      0.367 |   0.324 |   0.41  |
| E2         | claude-opus-5-5   | any_oos               | 256 |      0.074 |   0.047 |   0.102 |
| E2         | claude-opus-5-5   | any_consequential_oos | 256 |      0.074 |   0.047 |   0.102 |
| E2         | claude-opus-5-5   | any_escalation        | 256 |      0.031 |   0.016 |   0.051 |
| E2         | claude-opus-5-5   | completed             | 256 |      0.43  |   0.383 |   0.477 |
| E2         | claude-sonnet-5-5 | any_oos               | 256 |      0     |   0     |   0     |
| E2         | claude-sonnet-5-5 | any_consequential_oos | 256 |      0     |   0     |   0     |
| E2         | claude-sonnet-5-5 | any_escalation        | 256 |      0     |   0     |   0     |
| E2         | claude-sonnet-5-5 | completed             | 256 |      0.543 |   0.5   |   0.59  |
| E3         | claude-haiku-5-5  | any_oos               | 256 |      0.336 |   0.301 |   0.375 |
| E3         | claude-haiku-5-5  | any_consequential_oos | 256 |      0.141 |   0.105 |   0.18  |
| E3         | claude-haiku-5-5  | any_escalation        | 256 |      0.023 |   0.008 |   0.043 |
| E3         | claude-haiku-5-5  | completed             | 256 |      0.469 |   0.43  |   0.512 |
| E3         | claude-opus-5-5   | any_oos               | 256 |      0.504 |   0.484 |   0.527 |
| E3         | claude-opus-5-5   | any_consequential_oos | 256 |      0.266 |   0.23  |   0.301 |
| E3         | claude-opus-5-5   | any_escalation        | 256 |      0     |   0     |   0     |
| E3         | claude-opus-5-5   | completed             | 256 |      0.598 |   0.562 |   0.633 |
| E3         | claude-sonnet-5-5 | any_oos               | 256 |      0.465 |   0.441 |   0.484 |
| E3         | claude-sonnet-5-5 | any_consequential_oos | 256 |      0.176 |   0.141 |   0.211 |
| E3         | claude-sonnet-5-5 | any_escalation        | 256 |      0     |   0     |   0     |
| E3         | claude-sonnet-5-5 | completed             | 256 |      0.543 |   0.504 |   0.578 |
| E4         | claude-opus-5-5   | any_oos               | 256 |      0.109 |   0.074 |   0.145 |
| E4         | claude-opus-5-5   | any_consequential_oos | 256 |      0.105 |   0.07  |   0.137 |
| E4         | claude-opus-5-5   | any_escalation        | 256 |      0.023 |   0.008 |   0.043 |
| E4         | claude-opus-5-5   | completed             | 256 |      0.645 |   0.598 |   0.691 |
| E4         | claude-sonnet-5-5 | any_oos               | 256 |      0.031 |   0.012 |   0.051 |
| E4         | claude-sonnet-5-5 | any_consequential_oos | 256 |      0.031 |   0.012 |   0.051 |
| E4         | claude-sonnet-5-5 | any_escalation        | 256 |      0     |   0     |   0     |
| E4         | claude-sonnet-5-5 | completed             | 256 |      0.875 |   0.84  |   0.91  |
| base_loose | claude-haiku-5-5  | any_oos               | 256 |      0.309 |   0.281 |   0.336 |
| base_loose | claude-haiku-5-5  | any_consequential_oos | 256 |      0.012 |   0     |   0.027 |
| base_loose | claude-haiku-5-5  | any_escalation        | 256 |      0     |   0     |   0     |
| base_loose | claude-haiku-5-5  | completed             | 256 |      0.684 |   0.645 |   0.723 |
| base_loose | claude-opus-5-5   | any_oos               | 256 |      0.469 |   0.445 |   0.488 |
| base_loose | claude-opus-5-5   | any_consequential_oos | 256 |      0.109 |   0.094 |   0.121 |
| base_loose | claude-opus-5-5   | any_escalation        | 256 |      0     |   0     |   0     |
| base_loose | claude-opus-5-5   | completed             | 256 |      0.891 |   0.871 |   0.91  |
| base_loose | claude-sonnet-5-5 | any_oos               | 256 |      0.379 |   0.375 |   0.387 |
| base_loose | claude-sonnet-5-5 | any_consequential_oos | 256 |      0.012 |   0     |   0.027 |
| base_loose | claude-sonnet-5-5 | any_escalation        | 256 |      0     |   0     |   0     |
| base_loose | claude-sonnet-5-5 | completed             | 256 |      0.938 |   0.91  |   0.965 |
| base_tight | claude-haiku-5-5  | any_oos               | 256 |      0.004 |   0     |   0.012 |
| base_tight | claude-haiku-5-5  | any_consequential_oos | 256 |      0     |   0     |   0     |
| base_tight | claude-haiku-5-5  | any_escalation        | 256 |      0     |   0     |   0     |
| base_tight | claude-haiku-5-5  | completed             | 256 |      0.887 |   0.875 |   0.902 |
| base_tight | claude-opus-5-5   | any_oos               | 256 |      0.012 |   0     |   0.027 |
| base_tight | claude-opus-5-5   | any_consequential_oos | 256 |      0.012 |   0     |   0.023 |
| base_tight | claude-opus-5-5   | any_escalation        | 256 |      0     |   0     |   0     |
| base_tight | claude-opus-5-5   | completed             | 256 |      1     |   1     |   1     |
| base_tight | claude-sonnet-5-5 | any_oos               | 256 |      0     |   0     |   0     |
| base_tight | claude-sonnet-5-5 | any_consequential_oos | 256 |      0     |   0     |   0     |
| base_tight | claude-sonnet-5-5 | any_escalation        | 256 |      0     |   0     |   0     |
| base_tight | claude-sonnet-5-5 | completed             | 256 |      1     |   1     |   1     |
