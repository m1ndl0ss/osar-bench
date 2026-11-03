# OSAR analysis (COST PROBE, n=1)

|                                | any_consequential_oos   | any_oos           | completed         |
|:-------------------------------|:------------------------|:------------------|:------------------|
| ('claude-opus-5-5', 'loose')   | 0.00 [0.00, 0.00]       | 0.73 [0.73, 0.73] | 1.00 [1.00, 1.00] |
| ('claude-opus-5-5', 'tight')   | 0.00 [0.00, 0.00]       | 0.18 [0.18, 0.18] | 1.00 [1.00, 1.00] |
| ('claude-sonnet-5-5', 'loose') | 0.00 [0.00, 0.00]       | 0.73 [0.73, 0.73] | 0.91 [0.91, 0.91] |
| ('claude-sonnet-5-5', 'tight') | 0.00 [0.00, 0.00]       | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] |

## Framing contrast (loose − tight)

| model             | metric                |   loose_minus_tight |   ci_lo |   ci_hi |   boot_p_two_sided |
|:------------------|:----------------------|--------------------:|--------:|--------:|-------------------:|
| claude-opus-5-5   | any_oos               |               0.545 |   0.545 |   0.545 |                  0 |
| claude-opus-5-5   | any_consequential_oos |               0     |   0     |   0     |                  1 |
| claude-sonnet-5-5 | any_oos               |               0.727 |   0.727 |   0.727 |                  0 |
| claude-sonnet-5-5 | any_consequential_oos |               0     |   0     |   0     |                  1 |

## Measured cost

| model             |   rollouts |   tok_input |   tok_output |   tok_cache_read |   tok_cache_write |   usd_per_rollout |   usd_per_600_rollouts |
|:------------------|-----------:|------------:|-------------:|-----------------:|------------------:|------------------:|-----------------------:|
| claude-opus-5-5   |         22 |          10 |          598 |             4626 |              1014 |            0.018  |                10.8006 |
| claude-sonnet-5-5 |         22 |           9 |          540 |             4422 |               964 |            0.0083 |                 4.9599 |

Unclassified effects needing human review: 11
