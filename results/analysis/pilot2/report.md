# OSAR analysis (PILOT 2, Haiku, n=3)

|                               | any_consequential_oos   | any_oos           | completed         |
|:------------------------------|:------------------------|:------------------|:------------------|
| ('claude-haiku-5-5', 'loose') | 0.00 [0.00, 0.00]       | 0.58 [0.48, 0.67] | 0.76 [0.73, 0.82] |
| ('claude-haiku-5-5', 'tight') | 0.00 [0.00, 0.00]       | 0.06 [0.00, 0.09] | 0.94 [0.91, 1.00] |

## Framing contrast (loose − tight)

| model            | metric                |   loose_minus_tight |   ci_lo |   ci_hi |   boot_p_two_sided |
|:-----------------|:----------------------|--------------------:|--------:|--------:|-------------------:|
| claude-haiku-5-5 | any_oos               |               0.515 |   0.394 |   0.606 |                  0 |
| claude-haiku-5-5 | any_consequential_oos |               0     |   0     |   0     |                  1 |

## Measured cost

| model            |   rollouts |   tok_input |   tok_output |   tok_cache_read |   tok_cache_write |   usd_per_rollout |   usd_per_600_rollouts |
|:-----------------|-----------:|------------:|-------------:|-----------------:|------------------:|------------------:|-----------------------:|
| claude-haiku-5-5 |         66 |           9 |          687 |             4927 |               851 |            0.0005 |                    0.3 |

Unclassified effects needing human review: 30
