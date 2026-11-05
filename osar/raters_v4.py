"""Three independent, blind model raters on the v1-v4 coding sheet (a study instrument, not a human study).

  python -m osar.raters_v4 --sheet prereg/coding_sheet_v4.csv --model claude-opus-5-5 --out results/analysis/supplementary

Each rater sees only the fixed prompt in prereg/rater_prompt.txt (which embeds RATER_GUIDE.md) and the sheet's
columns, ten items per call, never the key or another rater's labels. Temperature 0 is requested; if the API
rejects the parameter the call is repeated at the default sampling and that is recorded in the usage file.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd

from .models import _retry

ROOT = Path(__file__).resolve().parent.parent
COLS = ["item", "version", "task_id", "framing", "condition", "prompt", "tool", "op", "target", "command", "denied"]


def item_text(r) -> str:
    cmd = f" command: {r.command}" if isinstance(r.command, str) and r.command else ""
    denied = " (denied by the sandbox)" if isinstance(r.denied, str) and r.denied == "yes" else ""
    return (f'item {r.item}: {r.version}, {r.task_id}, {r.framing} wording, condition {r.condition}\n'
            f'  request: "{r.prompt}"\n  effect: tool={r.tool} op={r.op} target={r.target}{cmd}{denied}')


def parse(out: str) -> dict:
    labels = {}
    m = re.search(r"\[.*\]", out, re.S)
    if m:
        try:
            for d in json.loads(m.group(0)):
                if str(d.get("label", "")).lower() in ("in_scope", "gray", "oos"):
                    labels[int(d["item"])] = d["label"].lower()
        except (ValueError, KeyError, TypeError):
            pass
    return labels


class Rater:
    def __init__(self, model: str, prompt: str):
        import anthropic
        headers = {"anthropic-workspace-id": os.environ["OSAR_ANTHROPIC_WORKSPACE"]} if os.environ.get("OSAR_ANTHROPIC_WORKSPACE") else {}
        self.client = anthropic.Anthropic(api_key=os.environ["OSAR_ANTHROPIC_KEY"], default_headers=headers)
        self.model, self.prompt = model, prompt
        self.temperature = "0"
        self.usage = {"calls": 0, "input": 0, "output": 0, "cache_read": 0}

    def call(self, text: str) -> str:
        kw = dict(model=self.model, max_tokens=800, system=self.prompt, thinking={"type": "adaptive"},
                  output_config={"effort": "low"}, messages=[{"role": "user", "content": text}])
        try:
            resp = _retry(lambda: self.client.messages.create(temperature=0.0, **kw)) if self.temperature == "0" else _retry(lambda: self.client.messages.create(**kw))
        except Exception as e:  # noqa: BLE001
            if self.temperature == "0" and "temperature" in str(e).lower():
                self.temperature = "default (temperature rejected by the API)"
                resp = _retry(lambda: self.client.messages.create(**kw))
            else:
                raise
        u = resp.usage
        self.usage["calls"] += 1
        self.usage["input"] += u.input_tokens
        self.usage["output"] += u.output_tokens
        self.usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
        return "\n".join(b.text for b in resp.content if b.type == "text")

    def label(self, batch: pd.DataFrame) -> dict:
        return parse(self.call("Label these effects.\n\n" + "\n".join(item_text(r) for r in batch.itertuples())))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=10)
    a = ap.parse_args(argv)
    sheet = pd.read_csv(a.sheet)[COLS]
    rater = Rater(a.model, (ROOT / "prereg/rater_prompt.txt").read_text())
    labels = {}
    for i in range(0, len(sheet), a.batch):
        labels.update(rater.label(sheet.iloc[i:i + a.batch]))
    for it in [it for it in sheet.item if it not in labels]:  # one retry, one item per call
        labels.update(rater.label(sheet[sheet.item == it]))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"item": sheet.item, "label": [labels.get(it, "") for it in sheet.item]}).to_csv(out / f"rater_v4_{a.model}.csv", index=False)
    (out / f"rater_v4_{a.model}_usage.json").write_text(json.dumps({"model": a.model, "temperature": rater.temperature, **rater.usage}, indent=1))
    print(a.model, "labelled", sum(1 for it in sheet.item if it in labels), "of", len(sheet), "| usage", rater.usage, "| temperature:", rater.temperature)


if __name__ == "__main__":
    main()
