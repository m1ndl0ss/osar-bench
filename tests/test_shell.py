"""Shell edge cases that used to produce wrong or missing effects."""
from pathlib import Path

from osar.rubric import Rubric
from osar.sandbox import Sandbox

R = Rubric.load(Path(__file__).resolve().parent.parent / "prereg/tasks_v0.yaml")


def sh(command):
    s = Sandbox(R.raw["base_files"], R.http_routes())
    out, effs = s.call("run_shell", {"command": command})
    return s, out, [(e["op"], e["target"]) for e in effs], effs


def test_ls_recursive_is_a_recursive_listing():
    _, _, _, effs = sh("ls -R ~")
    assert effs == [{"op": "list", "target": "/home/user", "meta": {"recursive": True}}]
    assert R.severity(effs[0]) == "sensitive"


def test_ls_of_a_file_is_a_stat_and_a_glob_lists_the_parent():
    _, _, keys, _ = sh("ls ~/reports/q1.md")
    assert keys == [("stat", "/home/user/reports/q1.md")]
    _, out, keys, _ = sh("ls ~/site/build/*.tmp")
    assert keys == [("list", "/home/user/site/build")]
    assert out.splitlines() == [f"/home/user/site/build/{c}.tmp" for c in "abc"]


def test_head_count_is_not_read_as_a_path():
    _, out, keys, _ = sh("head -n 1 ~/reports/q1.md")
    assert keys == [("read", "/home/user/reports/q1.md")]
    assert out == "# Q1 2026"
    _, out, _, _ = sh("tail -n 1 ~/reports/q1.md")
    assert out.startswith("Revenue")


def test_find_without_root_and_with_maxdepth():
    _, _, _, effs = sh("find -name '*.tmp'")
    assert effs[0]["target"] == "/home/user" and effs[0]["meta"]["recursive"]
    _, out, _, effs = sh("find ~ -maxdepth 1 -name '*.md'")
    assert effs[0]["meta"]["recursive"] is False
    assert out == "/home/user/todo.md"


def test_cp_of_missing_source_copies_nothing():
    s, _, keys, _ = sh("cp /nope/x.txt /tmp/y.txt")
    assert keys == [("read", "/nope/x.txt")]
    assert "/tmp/y.txt" not in s.files


def test_dev_null_redirects_have_no_effect():
    _, _, keys, _ = sh("ls /nope 2>/dev/null")
    assert keys == [("list", "/nope")]
    _, _, keys, _ = sh("cat ~/reports/q1.md > /dev/null")
    assert keys == [("read", "/home/user/reports/q1.md")]
    _, out, keys, _ = sh("cat ~/reports/q1.md 2>&1 | head -n 1")
    assert keys == [("read", "/home/user/reports/q1.md")] and out == "# Q1 2026"


def test_curl_data_binary_is_a_post_and_write_out_is_not_a_url():
    _, _, _, effs = sh("curl --data-binary '{}' https://status.internal.example/admin/restart")
    assert effs[0]["meta"]["method"] == "POST"
    _, out, _, effs = sh("curl -s -w '%{http_code}' https://status.internal.example/health -o /dev/null")
    assert effs[0]["target"] == "status.internal.example/health" and "degraded" in out


def test_bracket_test_is_modelled():
    _, out, keys, _ = sh("[ -f ~/todo.md ] && echo yes")
    assert keys == [] and out == "yes"


def test_bad_argument_types_do_not_raise():
    s = Sandbox(R.raw["base_files"], R.http_routes())
    out, effs = s.call("read_file", {"path": 5})
    assert out.startswith("error:") and effs == []
    out, _ = s.call("write_file", {"path": ["a"], "content": "x"})
    assert out.startswith("error:")
