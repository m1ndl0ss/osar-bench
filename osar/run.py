"""Run rollouts and write one JSON log per rollout.

Example (pilot, cheapest model):
  python -m osar.run --provider anthropic --model claude-haiku-5-5 --n 5 --out results/raw/pilot
Grok (run where api.x.ai is reachable, with XAI_API_KEY set):
  python -m osar.run --provider xai --model grok-4.6 --n 5 --out results/raw/pilot
Dry run, no API spend:
  python -m osar.run --provider scripted --model scripted-p0.3 --n 25 --out results/raw/dryrun
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import threading

from .models import make_adapter
from .pricing import usd
from .rubric import Rubric
from .sandbox import Sandbox
from .tools import TOOLS

ROOT = Path(__file__).resolve().parent.parent


def _git_rev() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:  # noqa: BLE001
        return "uncommitted"


def run_rollout(rubric: Rubric, task_id: str, framing: str, provider: str, model: str,
                seed: int, extra: dict | None, max_tokens: int, meter: list | None = None) -> dict:
    """meter: list that receives every step's usage as it happens (so spend is
    counted even if the rollout later crashes)."""
    meter = meter if meter is not None else []
    task = rubric.tasks[task_id]
    prompt = task["prompts"][framing]
    system = rubric.raw["system_prompt"]
    sb = Sandbox(rubric.raw["base_files"], rubric.http_routes())
    base_files = dict(sb.files)
    adapter = make_adapter(provider, model, system, prompt, task_id, framing, seed, extra, max_tokens)

    steps, final_text, status = [], "", "max_steps"
    t0 = time.time()
    for k in range(rubric.raw["max_steps"]):
        res = adapter.step()
        meter.append(res.usage)
        step = {"step": k, "text": res.text, "stop": res.stop, "usage": res.usage,
                "response_id": res.raw_id, "calls": []}
        if not res.tool_calls:
            final_text, status = res.text, "finished"
            steps.append(step)
            break
        results = []
        for c in res.tool_calls:
            out, effects = sb.call(c["name"], c["args"] if isinstance(c["args"], dict) else {})
            step["calls"].append({"id": c["id"], "name": c["name"], "args": c["args"],
                                  "output": out, "effects": effects})
            results.append({"id": c["id"], "name": c["name"], "output": out})
        adapter.add_tool_results(results)
        steps.append(step)

    changed = {p: sb.files[p] for p in sb.files if base_files.get(p) != sb.files[p]}
    deleted = sorted(p for p in base_files if p not in sb.files)
    return {
        "schema": "osar-rollout/1",
        "task_id": task_id, "framing": framing, "prompt": prompt, "seed": seed,
        "provider": provider, "model": model, "settings": {"max_tokens": max_tokens, **(extra or {})},
        "rubric_sha256": rubric.sha256, "rubric_version": rubric.raw["version"],
        "tools_sha256": hashlib.sha256(json.dumps(TOOLS, sort_keys=True).encode()).hexdigest(),
        "harness_git": _git_rev(), "python": platform.python_version(),
        "started_utc": dt.datetime.fromtimestamp(t0, dt.timezone.utc).isoformat(),
        "wall_seconds": round(time.time() - t0, 2),
        "status": status, "final_text": final_text, "steps": steps,
        "cost_usd": round(sum(usd(model, u) for u in meter), 6),
        "final_state": {"changed_files": changed, "deleted_files": deleted, "outbox": sb.outbox},
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", default=str(ROOT / "prereg/tasks_v0.yaml"))
    ap.add_argument("--provider", required=True, choices=["anthropic", "xai", "openai_compat", "scripted"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--tasks", default="all")
    ap.add_argument("--framings", default="tight,loose")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--extra", default="{}", help="JSON of extra provider params, recorded in logs")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-usd", type=float, default=2.0,
                    help="stop launching rollouts once THIS invocation has spent this much")
    ap.add_argument("--global-cap", type=float, default=50.0,
                    help="stop once the all-time ledger total reaches this (project hard cap)")
    ap.add_argument("--ledger", default=str(ROOT / "results/spend_ledger.jsonl"))
    ap.add_argument("--yes", action="store_true", help="skip the spend confirmation")
    a = ap.parse_args(argv)

    rubric = Rubric.load(a.rubric)
    tasks = list(rubric.tasks) if a.tasks == "all" else a.tasks.split(",")
    extra = json.loads(a.extra)
    # pre-registered: lowest reasoning setting each API accepts, thinking left on
    if a.provider == "anthropic":
        extra.setdefault("thinking", {"type": "adaptive"})
        extra.setdefault("output_config", {"effort": "low"})
    elif a.provider == "xai":
        extra.setdefault("reasoning_effort", "low")
    out = Path(a.out) / a.model
    out.mkdir(parents=True, exist_ok=True)

    jobs = []
    for t in tasks:
        for f in a.framings.split(","):
            for i in range(a.n):
                path = out / f"{t}__{f}__{a.seed0 + i:03d}.json"
                if path.exists():
                    continue  # resumable
                jobs.append((t, f, a.seed0 + i, path))
    ledger = Path(a.ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    hist = ([json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
            if ledger.exists() else [])
    spent_total = sum(h["usd"] for h in hist)
    same = [h["usd"] for h in hist if h["model"] == a.model and h.get("ok") and h.get("task_id") != "probe"]
    est = (sum(same) / len(same) * len(jobs)) if same else None
    print(f"{len(jobs)} rollouts to run -> {out}", file=sys.stderr)
    print(f"ledger total so far: ${spent_total:.4f} (global cap ${a.global_cap:.2f}); "
          f"this run capped at ${a.max_usd:.2f}; estimate: "
          + (f"${est:.4f} from {len(same)} past {a.model} rollouts" if est is not None else "unknown (no history)"),
          file=sys.stderr)
    if a.provider != "scripted" and not a.yes:
        if input("Proceed? [y/N] ").strip().lower() != "y":
            sys.exit("aborted")
    lock = threading.Lock()
    spent = {"run": 0.0, "total": spent_total}

    def book(t, f, seed, meter, ok):
        cost = sum(usd(a.model, u) for u in meter)
        if a.provider == "scripted":
            return
        with lock:
            spent["run"] += cost
            spent["total"] += cost
            with ledger.open("a") as fh:
                fh.write(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                     "model": a.model, "task_id": t, "framing": f, "seed": seed,
                                     "usd": round(cost, 6), "ok": ok}) + "\n")

    def over_cap():
        return spent["run"] >= a.max_usd or spent["total"] >= a.global_cap

    def work(job):
        t, f, seed, path = job
        if over_cap():
            return path.name, "SKIPPED (spend cap reached)"
        meter: list = []
        try:
            rec = run_rollout(rubric, t, f, a.provider, a.model, seed, extra, a.max_tokens, meter)
            book(t, f, seed, meter, True)
        except Exception as e:  # noqa: BLE001
            book(t, f, seed, meter, False)
            err = out / "errors"
            err.mkdir(exist_ok=True)
            (err / path.name).write_text(json.dumps(
                {"task_id": t, "framing": f, "seed": seed, "error": repr(e),
                 "trace": traceback.format_exc()}, indent=1))
            return path.name, "ERROR " + repr(e)[:120]
        path.write_text(json.dumps(rec, indent=1))
        return path.name, rec["status"]

    done = 0
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        for fut in as_completed([ex.submit(work, j) for j in jobs]):
            name, st = fut.result()
            done += 1
            print(f"[{done}/{len(jobs)}] {name}: {st}  (run ${spent['run']:.4f})", file=sys.stderr)
    print(f"spent this run: ${spent['run']:.4f}; ledger total: ${spent['total']:.4f}", file=sys.stderr)


if __name__ == "__main__":
    main()
