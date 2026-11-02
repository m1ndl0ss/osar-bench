"""AnthropicAdapter and runner tests against a fake Anthropic client. No network."""
import json
import os

import anthropic
import pytest
from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

from osar import run
from osar.models import AnthropicAdapter


def message(content, stop, input_tokens=1000, output_tokens=50):
    return Message(id="msg_1", type="message", role="assistant", model="claude-haiku-5-5",
                   content=content, stop_reason=stop, stop_sequence=None,
                   usage=Usage(input_tokens=input_tokens, output_tokens=output_tokens,
                               cache_read_input_tokens=0, cache_creation_input_tokens=0))


def text(s):
    return TextBlock(type="text", text=s)


def tool_use(id, name, **args):
    return ToolUseBlock(type="tool_use", id=id, name=name, input=args)


class FakeMessages:
    """Returns the scripted responses in order; the last one repeats."""

    def __init__(self, script):
        self.script, self.requests = list(script), []

    def create(self, **kw):
        self.requests.append(json.loads(json.dumps(kw)))  # snapshot, the adapter reuses its lists
        return self.script.pop(0) if len(self.script) > 1 else self.script[0]


class FakeClient:
    def __init__(self, script, **kw):
        self.kwargs = kw
        self.messages = FakeMessages(script)


@pytest.fixture
def fake(monkeypatch):
    """Install a fake anthropic.Anthropic; returns the list of clients it made."""
    made = []
    state = {"script": None}

    def factory(**kw):
        made.append(FakeClient(state["script"], **kw))
        return made[-1]

    monkeypatch.setenv("OSAR_ANTHROPIC_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(anthropic, "Anthropic", factory)

    def install(script):
        state["script"] = script
        return made
    return install


def count_breakpoints(req):
    n = sum("cache_control" in b for b in req["system"])
    n += sum("cache_control" in t for t in req["tools"])
    n += sum("cache_control" in b for m in req["messages"] for b in m["content"])
    return n


def check_sequence(msgs):
    """Messages alternate user/assistant and every tool_use is answered by a
    tool_result with the same id in the very next (user) message."""
    assert msgs[0]["role"] == "user" and msgs[-1]["role"] == "user"
    for i, m in enumerate(msgs):
        assert m["role"] == ("user" if i % 2 == 0 else "assistant")
        if m["role"] != "assistant":
            continue
        ids = [b["id"] for b in m["content"] if b["type"] == "tool_use"]
        if ids:
            nxt = msgs[i + 1]["content"]
            assert all(b["type"] == "tool_result" for b in nxt)
            assert [b["tool_use_id"] for b in nxt] == ids


def test_adapter_builds_valid_message_sequences(fake):
    made = fake([
        message([text("Looking."), tool_use("toolu_1", "read_file", path="/a"),
                 tool_use("toolu_2", "list_dir", path="/b")], "tool_use"),
        message([tool_use("toolu_3", "write_file", path="/c", content="x")], "tool_use"),
        message([text("Done.")], "end_turn"),
    ])
    a = AnthropicAdapter("claude-haiku-5-5", "sys prompt", "do the task",
                         extra={"thinking": {"type": "disabled"}})
    seen = []
    for _ in range(5):
        r = a.step()
        seen.append(r)
        if not r.tool_calls:
            break
        a.add_tool_results([{"id": c["id"], "name": c["name"], "output": "ok"} for c in r.tool_calls])
    assert [r.stop for r in seen] == ["tool_use", "tool_use", "end_turn"]
    assert seen[0].text == "Looking." and [c["name"] for c in seen[0].tool_calls] == ["read_file", "list_dir"]
    assert seen[0].tool_calls[0]["args"] == {"path": "/a"}
    assert seen[0].usage == {"input": 1000, "output": 50, "cache_read": 0, "cache_write": 0}

    reqs = made[0].messages.requests
    assert len(reqs) == 3 and made[0].kwargs["api_key"] == "test-key"
    for req in reqs:
        assert req["model"] == "claude-haiku-5-5" and req["max_tokens"] == 4096
        assert req["thinking"] == {"type": "disabled"}
        assert len(req["tools"]) == 8 and all("input_schema" in t for t in req["tools"])
        check_sequence(req["messages"])
        assert count_breakpoints(req) == 3 <= 4
        assert "cache_control" in req["messages"][-1]["content"][-1]
    assert len(reqs[2]["messages"]) == 5
    # breakpoints are added on a copy, so they never pile up in the kept history
    assert not any("cache_control" in b for m in a.messages for b in m["content"])


def run_args(tmp_path, n, max_usd):
    return ["--provider", "anthropic", "--model", "claude-haiku-5-5", "--tasks", "T3_check_status",
            "--framings", "tight", "--n", str(n), "--max-usd", str(max_usd), "--concurrency", "1",
            "--yes", "--out", str(tmp_path / "raw"), "--ledger", str(tmp_path / "ledger.jsonl")]


def test_runner_stops_launching_at_max_usd(fake, tmp_path, capsys):
    # 1M input tokens at Haiku rates is $0.10 per rollout
    fake([message([text("fine")], "end_turn", input_tokens=1_000_000, output_tokens=10)])
    run.main(run_args(tmp_path, n=4, max_usd=0.15))
    logs = sorted((tmp_path / "raw" / "claude-haiku-5-5").glob("*.json"))
    assert [p.name for p in logs] == ["T3_check_status__tight__000.json", "T3_check_status__tight__001.json"]
    ledger = [json.loads(l) for l in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert len(ledger) == 2 and all(abs(e["usd"] - 0.100005) < 1e-6 and e["ok"] for e in ledger)
    assert capsys.readouterr().err.count("SKIPPED") == 2
    rec = json.loads(logs[0].read_text())
    assert rec["settings"] == {"max_tokens": 4096, "thinking": {"type": "disabled"}}
    assert rec["status"] == "finished" and abs(rec["cost_usd"] - 0.100005) < 1e-6


def test_runner_respects_global_cap_from_ledger(fake, tmp_path, capsys):
    fake([message([text("fine")], "end_turn")])
    (tmp_path / "ledger.jsonl").write_text(json.dumps({"model": "x", "usd": 50.0, "ok": True}) + "\n\n")
    run.main(run_args(tmp_path, n=3, max_usd=1.0))
    assert not list((tmp_path / "raw").rglob("*.json"))
    assert capsys.readouterr().err.count("SKIPPED") == 3
