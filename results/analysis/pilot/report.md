# OSAR analysis (PILOT, Haiku, n=3)

|                               | any_consequential_oos   | any_oos           | completed         |
|:------------------------------|:------------------------|:------------------|:------------------|
| ('claude-haiku-5-5', 'loose') | 0.12 [0.06, 0.18]       | 0.67 [0.58, 0.76] | 0.61 [0.52, 0.70] |
| ('claude-haiku-5-5', 'tight') | 0.00 [0.00, 0.00]       | 0.06 [0.00, 0.12] | 0.97 [0.91, 1.00] |

## Framing contrast (loose − tight)

| model            | metric                |   loose_minus_tight |   ci_lo |   ci_hi |   boot_p_two_sided |
|:-----------------|:----------------------|--------------------:|--------:|--------:|-------------------:|
| claude-haiku-5-5 | any_oos               |               0.606 |   0.485 |   0.697 |              0     |
| claude-haiku-5-5 | any_consequential_oos |               0.121 |   0.061 |   0.182 |              0.003 |

## Measured cost

| model            |   rollouts |   tok_input |   tok_output |   tok_cache_read |   tok_cache_write |   usd_per_rollout |   usd_per_600_rollouts |
|:-----------------|-----------:|------------:|-------------:|-----------------:|------------------:|------------------:|-----------------------:|
| claude-haiku-5-5 |         66 |           9 |          740 |             5033 |               793 |            0.0005 |                 0.3123 |

Unclassified effects needing human review: 91
