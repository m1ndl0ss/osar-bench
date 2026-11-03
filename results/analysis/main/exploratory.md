# EXPLORATORY analyses (not pre-registered; the confirmatory tables are in report.md)

No-op `mkdir` effects (directory already existed at the start): 3 out-of-scope consequential effects.

## Rates (task-macro-averaged share of rollouts, 95% bootstrap CI)

| metric                                  | model             | framing   |   n_rollouts |   estimate |   ci_lo |   ci_hi |
|:----------------------------------------|:------------------|:----------|-------------:|-----------:|--------:|--------:|
| any_consequential_oos excl. no-op mkdir | claude-haiku-5-5  | loose     |          352 |      0.009 |   0     |   0.017 |
| any_consequential_oos excl. no-op mkdir | claude-haiku-5-5  | tight     |          352 |      0     |   0     |   0     |
| any_consequential_oos excl. no-op mkdir | claude-opus-5-5   | loose     |          352 |      0.08  |   0.068 |   0.088 |
| any_consequential_oos excl. no-op mkdir | claude-opus-5-5   | tight     |          352 |      0     |   0     |   0     |
| any_consequential_oos excl. no-op mkdir | claude-sonnet-5-5 | loose     |          352 |      0.009 |   0     |   0.02  |
| any_consequential_oos excl. no-op mkdir | claude-sonnet-5-5 | tight     |          352 |      0     |   0     |   0     |
| any_oos | completed                     | claude-haiku-5-5  | loose     |          271 |      0.518 |   0.484 |   0.553 |
| any_oos | completed                     | claude-haiku-5-5  | tight     |          323 |      0.006 |   0     |   0.014 |
| any_oos | completed                     | claude-opus-5-5   | loose     |          324 |      0.534 |   0.519 |   0.545 |
| any_oos | completed                     | claude-opus-5-5   | tight     |          352 |      0.091 |   0.091 |   0.091 |
| any_oos | completed                     | claude-sonnet-5-5 | loose     |          336 |      0.56  |   0.538 |   0.582 |
| any_oos | completed                     | claude-sonnet-5-5 | tight     |          352 |      0     |   0     |   0     |
| any_consequential_oos | completed       | claude-haiku-5-5  | loose     |          271 |      0.012 |   0     |   0.025 |
| any_consequential_oos | completed       | claude-haiku-5-5  | tight     |          323 |      0     |   0     |   0     |
| any_consequential_oos | completed       | claude-opus-5-5   | loose     |          324 |      0.08  |   0.068 |   0.088 |
| any_consequential_oos | completed       | claude-opus-5-5   | tight     |          352 |      0.009 |   0     |   0.02  |
| any_consequential_oos | completed       | claude-sonnet-5-5 | loose     |          336 |      0.003 |   0     |   0.01  |
| any_consequential_oos | completed       | claude-sonnet-5-5 | tight     |          352 |      0     |   0     |   0     |

## Loose minus tight

| metric                                  | model             |   loose_minus_tight |   ci_lo |   ci_hi |
|:----------------------------------------|:------------------|--------------------:|--------:|--------:|
| any_consequential_oos excl. no-op mkdir | claude-haiku-5-5  |               0.009 |   0     |   0.02  |
| any_consequential_oos excl. no-op mkdir | claude-opus-5-5   |               0.08  |   0.068 |   0.088 |
| any_consequential_oos excl. no-op mkdir | claude-sonnet-5-5 |               0.009 |   0     |   0.02  |
| any_consequential_oos excl. no-op mkdir | pooled            |               0.032 |   0.023 |   0.042 |
| any_oos | completed                     | claude-haiku-5-5  |               0.512 |   0.477 |   0.548 |
| any_oos | completed                     | claude-opus-5-5   |               0.443 |   0.428 |   0.455 |
| any_oos | completed                     | claude-sonnet-5-5 |               0.56  |   0.538 |   0.582 |
| any_oos | completed                     | pooled            |               0.519 |   0.497 |   0.542 |
| any_consequential_oos | completed       | claude-haiku-5-5  |               0.012 |   0     |   0.025 |
| any_consequential_oos | completed       | claude-opus-5-5   |               0.071 |   0.057 |   0.082 |
| any_consequential_oos | completed       | claude-sonnet-5-5 |               0.003 |   0     |   0.01  |
| any_consequential_oos | completed       | pooled            |               0.046 |   0.033 |   0.059 |
