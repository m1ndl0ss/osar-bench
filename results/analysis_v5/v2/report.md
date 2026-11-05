# OSAR v2 addendum analysis (rubric v5)

## New tasks T12-T23, baseline harness (task-macro-averaged share of rollouts, 95% CI)

|                                | any_consequential_oos   | any_oos           | completed         |
|:-------------------------------|:------------------------|:------------------|:------------------|
| ('claude-haiku-5-5', 'loose')  | 0.00 [0.00, 0.00]       | 0.42 [0.39, 0.45] | 0.90 [0.89, 0.91] |
| ('claude-haiku-5-5', 'tight')  | 0.00 [0.00, 0.00]       | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |
| ('claude-opus-5-5', 'loose')   | 0.00 [0.00, 0.00]       | 0.40 [0.38, 0.41] | 0.96 [0.95, 0.98] |
| ('claude-opus-5-5', 'tight')   | 0.00 [0.00, 0.00]       | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |
| ('claude-sonnet-5-5', 'loose') | 0.01 [0.00, 0.01]       | 0.45 [0.43, 0.47] | 0.95 [0.93, 0.97] |
| ('claude-sonnet-5-5', 'tight') | 0.00 [0.00, 0.00]       | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |

## H4a / H4b: loose minus tight on the new tasks (one-sided p; Holm over the per-model tests)

| model             | metric                |   loose_minus_tight |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:------------------|:----------------------|--------------------:|--------:|--------:|--------------:|--------------:|---------:|
| claude-haiku-5-5  | any_oos               |               0.419 |   0.391 |   0.448 |         0     |         0     |    0     |
| claude-opus-5-5   | any_oos               |               0.396 |   0.378 |   0.414 |         0     |         0     |    0     |
| claude-sonnet-5-5 | any_oos               |               0.448 |   0.43  |   0.466 |         0     |         0     |    0     |
| pooled            | any_oos               |               0.421 |   0.405 |   0.437 |         0     |         0     |  nan     |
| claude-haiku-5-5  | any_consequential_oos |               0     |   0     |   0     |         1     |         1     |    1     |
| claude-opus-5-5   | any_consequential_oos |               0     |   0     |   0     |         1     |         1     |    1     |
| claude-sonnet-5-5 | any_consequential_oos |               0.005 |   0     |   0.013 |         0.119 |         0.239 |    0.358 |
| pooled            | any_consequential_oos |               0.002 |   0     |   0.004 |         0.131 |         0.262 |  nan     |

## H4c: Opus minus others, consequential OOS, loose framing, new tasks (one-sided; Holm)

| pair                                | metric                |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_holm |
|:------------------------------------|:----------------------|-------------:|--------:|--------:|--------------:|---------:|
| claude-opus-5-5 - claude-haiku-5-5  | any_consequential_oos |        0     |   0     |       0 |             1 |        1 |
| claude-opus-5-5 - claude-sonnet-5-5 | any_consequential_oos |       -0.005 |  -0.013 |       0 |             1 |        1 |

## H5: ask_user vs baseline, loose framing, all tasks (predicted lower; one-sided p; Holm)

| condition   | framing   | model             | metric                |   n_baseline |   n_condition |   baseline |   with_condition |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:------------|:----------|:------------------|:----------------------|-------------:|--------------:|-----------:|-----------------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| ask_user    | loose     | claude-haiku-5-5  | any_oos               |          736 |           736 |      0.37  |            0.367 |       -0.003 |  -0.027 |   0.022 |         0.432 |         0.864 |    0.864 |
| ask_user    | loose     | claude-opus-5-5   | any_oos               |          736 |           736 |      0.413 |            0.395 |       -0.018 |  -0.037 |   0.001 |         0.044 |         0.088 |    0.132 |
| ask_user    | loose     | claude-sonnet-5-5 | any_oos               |          736 |           736 |      0.409 |            0.417 |        0.008 |  -0.005 |   0.022 |         0.895 |         0.284 |    0.895 |
| ask_user    | loose     | pooled            | any_oos               |         2208 |          2208 |      0.397 |            0.393 |       -0.004 |  -0.018 |   0.01  |         0.29  |         0.58  |  nan     |
| ask_user    | loose     | claude-haiku-5-5  | any_consequential_oos |          736 |           736 |      0.004 |            0.014 |        0.01  |   0.001 |   0.019 |         0.991 |         0.039 |    1     |
| ask_user    | loose     | claude-opus-5-5   | any_consequential_oos |          736 |           736 |      0.038 |            0.029 |       -0.01  |  -0.019 |   0.001 |         0.045 |         0.09  |    0.135 |
| ask_user    | loose     | claude-sonnet-5-5 | any_consequential_oos |          736 |           736 |      0.007 |            0.007 |        0     |  -0.008 |   0.008 |         0.573 |         1     |    1     |
| ask_user    | loose     | pooled            | any_consequential_oos |         2208 |          2208 |      0.016 |            0.016 |        0     |  -0.007 |   0.007 |         0.52  |         1     |  nan     |

Ask rate and completion under ask_user (two-sided):

| condition   | framing   | model             | metric       |   n_baseline |   n_condition |   baseline |   with_condition |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:------------|:----------|:------------------|:-------------|-------------:|--------------:|-----------:|-----------------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| ask_user    | loose     | claude-haiku-5-5  | completed    |          736 |           736 |      0.837 |            0.774 |       -0.062 |  -0.082 |  -0.043 |           nan |         0     |      nan |
| ask_user    | loose     | claude-opus-5-5   | completed    |          736 |           736 |      0.943 |            0.944 |        0.001 |  -0.018 |   0.02  |           nan |         0.929 |      nan |
| ask_user    | loose     | claude-sonnet-5-5 | completed    |          736 |           736 |      0.954 |            0.886 |       -0.068 |  -0.088 |  -0.048 |           nan |         0     |      nan |
| ask_user    | loose     | pooled            | completed    |         2208 |          2208 |      0.911 |            0.868 |       -0.043 |  -0.058 |  -0.028 |           nan |         0     |      nan |
| ask_user    | loose     | claude-haiku-5-5  | any_ask_user |          736 |           736 |      0     |            0.084 |        0.084 |   0.071 |   0.098 |           nan |         0     |      nan |
| ask_user    | loose     | claude-opus-5-5   | any_ask_user |          736 |           736 |      0     |            0.031 |        0.031 |   0.02  |   0.043 |           nan |         0     |      nan |
| ask_user    | loose     | claude-sonnet-5-5 | any_ask_user |          736 |           736 |      0     |            0.048 |        0.048 |   0.037 |   0.058 |           nan |         0     |      nan |
| ask_user    | loose     | pooled            | any_ask_user |         2208 |          2208 |      0     |            0.054 |        0.054 |   0.047 |   0.062 |           nan |         0     |      nan |

## H6: scope instruction vs baseline, loose framing, all tasks (predicted lower; one-sided p; Holm)

| condition         | framing   | model             | metric                |   n_baseline |   n_condition |   baseline |   with_condition |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:------------------|:----------|:------------------|:----------------------|-------------:|--------------:|-----------:|-----------------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| scope_instruction | loose     | claude-haiku-5-5  | any_oos               |          736 |           736 |      0.37  |            0.299 |       -0.071 |  -0.095 |  -0.048 |         0     |         0     |    0     |
| scope_instruction | loose     | claude-opus-5-5   | any_oos               |          736 |           736 |      0.413 |            0.312 |       -0.101 |  -0.118 |  -0.082 |         0     |         0     |    0     |
| scope_instruction | loose     | claude-sonnet-5-5 | any_oos               |          736 |           736 |      0.409 |            0.391 |       -0.018 |  -0.031 |  -0.003 |         0.01  |         0.019 |    0.01  |
| scope_instruction | loose     | pooled            | any_oos               |         2208 |          2208 |      0.397 |            0.334 |       -0.063 |  -0.077 |  -0.048 |         0     |         0     |  nan     |
| scope_instruction | loose     | claude-haiku-5-5  | any_consequential_oos |          736 |           736 |      0.004 |            0.005 |        0.001 |  -0.005 |   0.008 |         0.716 |         0.86  |    0.716 |
| scope_instruction | loose     | claude-opus-5-5   | any_consequential_oos |          736 |           736 |      0.038 |            0.03  |       -0.008 |  -0.018 |   0.001 |         0.058 |         0.116 |    0.174 |
| scope_instruction | loose     | claude-sonnet-5-5 | any_consequential_oos |          736 |           736 |      0.007 |            0.003 |       -0.004 |  -0.011 |   0.003 |         0.168 |         0.336 |    0.336 |
| scope_instruction | loose     | pooled            | any_consequential_oos |         2208 |          2208 |      0.016 |            0.013 |       -0.004 |  -0.01  |   0.003 |         0.139 |         0.277 |  nan     |

Cost of the instruction: completion and clarification rate (two-sided):

| condition         | framing   | model             | metric        |   n_baseline |   n_condition |   baseline |   with_condition |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:------------------|:----------|:------------------|:--------------|-------------:|--------------:|-----------:|-----------------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| scope_instruction | loose     | claude-haiku-5-5  | completed     |          736 |           736 |      0.837 |            0.754 |       -0.083 |  -0.105 |  -0.061 |           nan |         0     |      nan |
| scope_instruction | loose     | claude-opus-5-5   | completed     |          736 |           736 |      0.943 |            0.909 |       -0.034 |  -0.052 |  -0.016 |           nan |         0     |      nan |
| scope_instruction | loose     | claude-sonnet-5-5 | completed     |          736 |           736 |      0.954 |            0.822 |       -0.132 |  -0.149 |  -0.114 |           nan |         0     |      nan |
| scope_instruction | loose     | pooled            | completed     |         2208 |          2208 |      0.911 |            0.828 |       -0.083 |  -0.098 |  -0.068 |           nan |         0     |      nan |
| scope_instruction | loose     | claude-haiku-5-5  | clarification |          736 |           736 |      0.043 |            0.037 |       -0.007 |  -0.024 |   0.01  |           nan |         0.476 |      nan |
| scope_instruction | loose     | claude-opus-5-5   | clarification |          736 |           736 |      0.001 |            0.038 |        0.037 |   0.026 |   0.048 |           nan |         0     |      nan |
| scope_instruction | loose     | claude-sonnet-5-5 | clarification |          736 |           736 |      0.007 |            0.052 |        0.045 |   0.033 |   0.057 |           nan |         0     |      nan |
| scope_instruction | loose     | pooled            | clarification |         2208 |          2208 |      0.017 |            0.042 |        0.025 |   0.016 |   0.034 |           nan |         0     |      nan |

## H7: friction vs baseline, tight framing, tasks T11_archive_logs, T1_summarize_reports, T2_fix_config_typo, T4_clean_tmp, T5_draft_reply, T6_rename_photos, T7_meeting_todos, T8_update_contact (predicted higher; one-sided p; Holm)

| condition   | framing   | model             | metric                |   n_baseline |   n_condition |   baseline |   with_condition |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:------------|:----------|:------------------|:----------------------|-------------:|--------------:|-----------:|-----------------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| friction    | tight     | claude-haiku-5-5  | any_oos               |          256 |           256 |      0.004 |            0.012 |        0.008 |  -0.008 |   0.023 |         0.23  |         0.459 |    0.23  |
| friction    | tight     | claude-opus-5-5   | any_oos               |          256 |           256 |      0.012 |            0.062 |        0.051 |   0.02  |   0.082 |         0     |         0.001 |    0.001 |
| friction    | tight     | claude-sonnet-5-5 | any_oos               |          256 |           256 |      0     |            0.137 |        0.137 |   0.105 |   0.168 |         0     |         0     |    0     |
| friction    | tight     | pooled            | any_oos               |          768 |           768 |      0.005 |            0.07  |        0.065 |   0.048 |   0.083 |         0     |         0     |  nan     |
| friction    | tight     | claude-haiku-5-5  | any_consequential_oos |          256 |           256 |      0     |            0.012 |        0.012 |   0     |   0.027 |         0.048 |         0.095 |    0.048 |
| friction    | tight     | claude-opus-5-5   | any_consequential_oos |          256 |           256 |      0.012 |            0.062 |        0.051 |   0.023 |   0.082 |         0     |         0     |    0     |
| friction    | tight     | claude-sonnet-5-5 | any_consequential_oos |          256 |           256 |      0     |            0.137 |        0.137 |   0.105 |   0.168 |         0     |         0     |    0     |
| friction    | tight     | pooled            | any_consequential_oos |          768 |           768 |      0.004 |            0.07  |        0.066 |   0.049 |   0.085 |         0     |         0     |  nan     |

Completion under friction (two-sided):

| condition   | framing   | model             | metric    |   n_baseline |   n_condition |   baseline |   with_condition |   difference |   ci_lo |   ci_hi |   p_one_sided |   p_two_sided |   p_holm |
|:------------|:----------|:------------------|:----------|-------------:|--------------:|-----------:|-----------------:|-------------:|--------:|--------:|--------------:|--------------:|---------:|
| friction    | tight     | claude-haiku-5-5  | completed |          256 |           256 |      0.887 |            0.547 |       -0.34  |  -0.383 |  -0.297 |           nan |             0 |      nan |
| friction    | tight     | claude-opus-5-5   | completed |          256 |           256 |      1     |            0.641 |       -0.359 |  -0.406 |  -0.312 |           nan |             0 |      nan |
| friction    | tight     | claude-sonnet-5-5 | completed |          256 |           256 |      1     |            0.781 |       -0.219 |  -0.266 |  -0.172 |           nan |             0 |      nan |
| friction    | tight     | pooled            | completed |          768 |           768 |      0.962 |            0.656 |       -0.306 |  -0.341 |  -0.271 |           nan |             0 |      nan |

Escalation under friction (share of rollouts):

| model             |   rollouts |   denied_once |   share_sudo |   share_chmod_chown |   share_gave_up |   completed |
|:------------------|-----------:|--------------:|-------------:|--------------------:|----------------:|------------:|
| claude-haiku-5-5  |        256 |         0.898 |        0.004 |                   0 |           0.352 |       0.547 |
| claude-opus-5-5   |        256 |         1     |        0.016 |                   0 |           0.359 |       0.641 |
| claude-sonnet-5-5 |        256 |         1     |        0.125 |                   0 |           0.219 |       0.781 |

## Rates by condition

| condition         | model             | framing   | metric                |   n_rollouts |   n_tasks |   estimate |   ci_lo |   ci_hi |
|:------------------|:------------------|:----------|:----------------------|-------------:|----------:|-----------:|--------:|--------:|
| ask_user          | claude-haiku-5-5  | loose     | any_oos               |          736 |        23 |      0.367 |   0.351 |   0.383 |
| ask_user          | claude-haiku-5-5  | loose     | any_consequential_oos |          736 |        23 |      0.014 |   0.007 |   0.022 |
| ask_user          | claude-haiku-5-5  | loose     | completed             |          736 |        23 |      0.774 |   0.762 |   0.787 |
| ask_user          | claude-haiku-5-5  | loose     | clarification         |          736 |        23 |      0.092 |   0.077 |   0.107 |
| ask_user          | claude-haiku-5-5  | loose     | any_ask_user          |          736 |        23 |      0.084 |   0.071 |   0.098 |
| ask_user          | claude-haiku-5-5  | loose     | any_oos_nonnav        |          736 |        23 |      0.292 |   0.277 |   0.306 |
| ask_user          | claude-opus-5-5   | loose     | any_oos               |          736 |        23 |      0.395 |   0.379 |   0.412 |
| ask_user          | claude-opus-5-5   | loose     | any_consequential_oos |          736 |        23 |      0.029 |   0.019 |   0.038 |
| ask_user          | claude-opus-5-5   | loose     | completed             |          736 |        23 |      0.944 |   0.929 |   0.959 |
| ask_user          | claude-opus-5-5   | loose     | clarification         |          736 |        23 |      0.012 |   0.005 |   0.02  |
| ask_user          | claude-opus-5-5   | loose     | any_ask_user          |          736 |        23 |      0.031 |   0.02  |   0.043 |
| ask_user          | claude-opus-5-5   | loose     | any_oos_nonnav        |          736 |        23 |      0.337 |   0.323 |   0.349 |
| ask_user          | claude-sonnet-5-5 | loose     | any_oos               |          736 |        23 |      0.417 |   0.408 |   0.428 |
| ask_user          | claude-sonnet-5-5 | loose     | any_consequential_oos |          736 |        23 |      0.007 |   0.001 |   0.012 |
| ask_user          | claude-sonnet-5-5 | loose     | completed             |          736 |        23 |      0.886 |   0.87  |   0.902 |
| ask_user          | claude-sonnet-5-5 | loose     | clarification         |          736 |        23 |      0.03  |   0.019 |   0.041 |
| ask_user          | claude-sonnet-5-5 | loose     | any_ask_user          |          736 |        23 |      0.048 |   0.037 |   0.058 |
| ask_user          | claude-sonnet-5-5 | loose     | any_oos_nonnav        |          736 |        23 |      0.33  |   0.321 |   0.34  |
| baseline          | claude-haiku-5-5  | loose     | any_oos               |          736 |        23 |      0.37  |   0.352 |   0.387 |
| baseline          | claude-haiku-5-5  | loose     | any_consequential_oos |          736 |        23 |      0.004 |   0     |   0.01  |
| baseline          | claude-haiku-5-5  | loose     | completed             |          736 |        23 |      0.837 |   0.822 |   0.852 |
| baseline          | claude-haiku-5-5  | loose     | clarification         |          736 |        23 |      0.043 |   0.031 |   0.056 |
| baseline          | claude-haiku-5-5  | loose     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-haiku-5-5  | loose     | any_oos_nonnav        |          736 |        23 |      0.279 |   0.264 |   0.295 |
| baseline          | claude-haiku-5-5  | tight     | any_oos               |          736 |        23 |      0.001 |   0     |   0.004 |
| baseline          | claude-haiku-5-5  | tight     | any_consequential_oos |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-haiku-5-5  | tight     | completed             |          736 |        23 |      0.961 |   0.957 |   0.965 |
| baseline          | claude-haiku-5-5  | tight     | clarification         |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-haiku-5-5  | tight     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-haiku-5-5  | tight     | any_oos_nonnav        |          736 |        23 |      0.001 |   0     |   0.004 |
| baseline          | claude-opus-5-5   | loose     | any_oos               |          736 |        23 |      0.413 |   0.401 |   0.424 |
| baseline          | claude-opus-5-5   | loose     | any_consequential_oos |          736 |        23 |      0.038 |   0.033 |   0.042 |
| baseline          | claude-opus-5-5   | loose     | completed             |          736 |        23 |      0.943 |   0.932 |   0.954 |
| baseline          | claude-opus-5-5   | loose     | clarification         |          736 |        23 |      0.001 |   0     |   0.004 |
| baseline          | claude-opus-5-5   | loose     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-opus-5-5   | loose     | any_oos_nonnav        |          736 |        23 |      0.365 |   0.355 |   0.375 |
| baseline          | claude-opus-5-5   | tight     | any_oos               |          736 |        23 |      0.004 |   0     |   0.01  |
| baseline          | claude-opus-5-5   | tight     | any_consequential_oos |          736 |        23 |      0.004 |   0     |   0.008 |
| baseline          | claude-opus-5-5   | tight     | completed             |          736 |        23 |      1     |   1     |   1     |
| baseline          | claude-opus-5-5   | tight     | clarification         |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-opus-5-5   | tight     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-opus-5-5   | tight     | any_oos_nonnav        |          736 |        23 |      0.004 |   0     |   0.008 |
| baseline          | claude-sonnet-5-5 | loose     | any_oos               |          736 |        23 |      0.409 |   0.399 |   0.418 |
| baseline          | claude-sonnet-5-5 | loose     | any_consequential_oos |          736 |        23 |      0.007 |   0.001 |   0.012 |
| baseline          | claude-sonnet-5-5 | loose     | completed             |          736 |        23 |      0.954 |   0.94  |   0.966 |
| baseline          | claude-sonnet-5-5 | loose     | clarification         |          736 |        23 |      0.007 |   0.001 |   0.014 |
| baseline          | claude-sonnet-5-5 | loose     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-sonnet-5-5 | loose     | any_oos_nonnav        |          736 |        23 |      0.349 |   0.337 |   0.361 |
| baseline          | claude-sonnet-5-5 | tight     | any_oos               |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-sonnet-5-5 | tight     | any_consequential_oos |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-sonnet-5-5 | tight     | completed             |          736 |        23 |      1     |   1     |   1     |
| baseline          | claude-sonnet-5-5 | tight     | clarification         |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-sonnet-5-5 | tight     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| baseline          | claude-sonnet-5-5 | tight     | any_oos_nonnav        |          736 |        23 |      0     |   0     |   0     |
| friction          | claude-haiku-5-5  | tight     | any_oos               |          256 |         8 |      0.012 |   0     |   0.027 |
| friction          | claude-haiku-5-5  | tight     | any_consequential_oos |          256 |         8 |      0.012 |   0     |   0.027 |
| friction          | claude-haiku-5-5  | tight     | completed             |          256 |         8 |      0.547 |   0.504 |   0.59  |
| friction          | claude-haiku-5-5  | tight     | clarification         |          256 |         8 |      0.016 |   0.004 |   0.031 |
| friction          | claude-haiku-5-5  | tight     | any_ask_user          |          256 |         8 |      0     |   0     |   0     |
| friction          | claude-haiku-5-5  | tight     | any_oos_nonnav        |          256 |         8 |      0.012 |   0     |   0.027 |
| friction          | claude-opus-5-5   | tight     | any_oos               |          256 |         8 |      0.062 |   0.039 |   0.09  |
| friction          | claude-opus-5-5   | tight     | any_consequential_oos |          256 |         8 |      0.062 |   0.035 |   0.09  |
| friction          | claude-opus-5-5   | tight     | completed             |          256 |         8 |      0.641 |   0.594 |   0.688 |
| friction          | claude-opus-5-5   | tight     | clarification         |          256 |         8 |      0.047 |   0.027 |   0.07  |
| friction          | claude-opus-5-5   | tight     | any_ask_user          |          256 |         8 |      0     |   0     |   0     |
| friction          | claude-opus-5-5   | tight     | any_oos_nonnav        |          256 |         8 |      0.062 |   0.035 |   0.09  |
| friction          | claude-sonnet-5-5 | tight     | any_oos               |          256 |         8 |      0.137 |   0.105 |   0.168 |
| friction          | claude-sonnet-5-5 | tight     | any_consequential_oos |          256 |         8 |      0.137 |   0.105 |   0.168 |
| friction          | claude-sonnet-5-5 | tight     | completed             |          256 |         8 |      0.781 |   0.738 |   0.824 |
| friction          | claude-sonnet-5-5 | tight     | clarification         |          256 |         8 |      0.035 |   0.016 |   0.059 |
| friction          | claude-sonnet-5-5 | tight     | any_ask_user          |          256 |         8 |      0     |   0     |   0     |
| friction          | claude-sonnet-5-5 | tight     | any_oos_nonnav        |          256 |         8 |      0.137 |   0.105 |   0.168 |
| scope_instruction | claude-haiku-5-5  | loose     | any_oos               |          736 |        23 |      0.299 |   0.283 |   0.315 |
| scope_instruction | claude-haiku-5-5  | loose     | any_consequential_oos |          736 |        23 |      0.005 |   0.001 |   0.011 |
| scope_instruction | claude-haiku-5-5  | loose     | completed             |          736 |        23 |      0.754 |   0.738 |   0.77  |
| scope_instruction | claude-haiku-5-5  | loose     | clarification         |          736 |        23 |      0.037 |   0.024 |   0.049 |
| scope_instruction | claude-haiku-5-5  | loose     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| scope_instruction | claude-haiku-5-5  | loose     | any_oos_nonnav        |          736 |        23 |      0.264 |   0.247 |   0.28  |
| scope_instruction | claude-opus-5-5   | loose     | any_oos               |          736 |        23 |      0.312 |   0.299 |   0.326 |
| scope_instruction | claude-opus-5-5   | loose     | any_consequential_oos |          736 |        23 |      0.03  |   0.022 |   0.038 |
| scope_instruction | claude-opus-5-5   | loose     | completed             |          736 |        23 |      0.909 |   0.895 |   0.923 |
| scope_instruction | claude-opus-5-5   | loose     | clarification         |          736 |        23 |      0.038 |   0.027 |   0.049 |
| scope_instruction | claude-opus-5-5   | loose     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| scope_instruction | claude-opus-5-5   | loose     | any_oos_nonnav        |          736 |        23 |      0.277 |   0.264 |   0.292 |
| scope_instruction | claude-sonnet-5-5 | loose     | any_oos               |          736 |        23 |      0.391 |   0.38  |   0.402 |
| scope_instruction | claude-sonnet-5-5 | loose     | any_consequential_oos |          736 |        23 |      0.003 |   0     |   0.007 |
| scope_instruction | claude-sonnet-5-5 | loose     | completed             |          736 |        23 |      0.822 |   0.811 |   0.834 |
| scope_instruction | claude-sonnet-5-5 | loose     | clarification         |          736 |        23 |      0.052 |   0.041 |   0.062 |
| scope_instruction | claude-sonnet-5-5 | loose     | any_ask_user          |          736 |        23 |      0     |   0     |   0     |
| scope_instruction | claude-sonnet-5-5 | loose     | any_oos_nonnav        |          736 |        23 |      0.311 |   0.3   |   0.322 |
