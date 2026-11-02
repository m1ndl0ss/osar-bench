"""USD per million tokens: (input, output, cache_read, cache_write_5m).
Checked 2026-11-02 against platform.claude.com/docs/en/about-claude/pricing and xAI's
pricing page. Haiku 5.5 rates are the <=100K-prompt tier. Re-check before the main run."""

PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0, 0.10, 2.50),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125),
    "grok-4.6": (2.0, 6.0, 0.50, 0.0),
}


def usd(model: str, usage: dict) -> float:
    p = PRICES.get(model)
    if p is None:
        return 0.0
    return (usage.get("input", 0) * p[0] + usage.get("output", 0) * p[1]
            + usage.get("cache_read", 0) * p[2] + usage.get("cache_write", 0) * p[3]) / 1e6
