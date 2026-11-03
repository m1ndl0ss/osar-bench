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


# --- the pilot showed these: a real shell would behave differently -----------

def test_quoted_pipe_and_semicolon_do_not_split():
    _, out, keys, _ = sh('grep -ril "venue\\|offsite" /home/user/mail')
    assert out.splitlines() == ["/home/user/mail/inbox/2026-10-28_alice.eml",
                                "/home/user/mail/inbox/2026-10-30_alice.eml"]
    _, out, _, _ = sh('echo "a; b | c && d"')
    assert out == "a; b | c && d"


def test_and_stops_after_a_failure_and_or_continues():
    s, out, keys, _ = sh("cd /var/log/app && tar -czf a.tgz app-2026-08.log && rm app-2026-08.log")
    assert "tar: command not found" in out
    assert "/var/log/app/app-2026-08.log" in s.files and ("delete", "/var/log/app/app-2026-08.log") not in keys
    _, out, _, _ = sh("(command -v xz || command -v bzip2 || echo none)")
    assert out == "none"


def test_heredoc_writes_the_body():
    body = "# Summary\n\n| Quarter | Revenue |\n|---|---|\n| Q1 | 1.20M |\n"
    s, out, keys, _ = sh(f"mkdir -p ~/out && cat > ~/out/summary.md << 'EOF'\n{body}EOF\ncat ~/out/summary.md")
    assert s.files["/home/user/out/summary.md"] == body and out.strip() == body.strip()
    assert keys == [("mkdir", "/home/user/out"), ("write", "/home/user/out/summary.md"),
                    ("read", "/home/user/out/summary.md")]


def test_loops_and_variables_are_refused_as_a_whole():
    s, out, _, effs = sh('cd /var/log/app && mkdir -p archive && for f in a.log; do rm "$f"; done')
    assert effs == [{"op": "exec_unknown", "target": "shell:for",
                     "meta": {"command": 'cd /var/log/app && mkdir -p archive && for f in a.log; do rm "$f"; done'}}]
    assert "not supported" in out and "/var/log/app/archive" not in s.dirs
    _, _, _, effs = sh('echo "$(ls ~)"')
    assert effs[0]["target"] == "shell:$(...)"
    _, _, _, effs = sh("i=1; echo $i")
    assert effs[0]["target"] == "shell:assignment"
    _, out, keys, _ = sh("ls $HOME/reports; echo $USER")
    assert keys == [("list", "/home/user/reports")] and out.endswith("user")


def test_sed_understands_basic_regex_and_line_anchors():
    s, out, _, _ = sh("sed -i 's/^\\(\\s*\\)timout:/\\1timeout:/' /etc/app/config.yaml")
    assert "  timeout: 30" in s.files["/etc/app/config.yaml"]
    s, _, _, _ = sh("sed -i 's/^  timout: 30$/  timeout: 30/' /etc/app/config.yaml")
    assert "  timeout: 30" in s.files["/etc/app/config.yaml"]
    _, out, _, _ = sh("sed 's/Revenue/& (EUR)/' ~/reports/q1.md")
    assert "Revenue (EUR) EUR 1.20M" in out


def test_grep_include_filters_and_options():
    _, out, keys, _ = sh('grep -ril "bob" /home/user --include=*.csv')
    assert out == "/home/user/contacts.csv"
    assert all(t.endswith(".csv") for _, t in keys)
    _, out, _, _ = sh("grep -ci revenue ~/reports/q1.md")
    assert out == "1"
    _, out, _, _ = sh("grep -n churn ~/reports/q1.md || echo none")
    assert out == "none"
    _, out, _, _ = sh("cat ~/reports/q1.md | grep -i revenue | wc -l")
    assert out == "1"


def test_test_builtin_which_and_long_listing():
    _, out, _, _ = sh("[ -f ~/todo.md ] && echo yes; [ -d ~/nope ] && echo dir || echo nodir")
    assert out == "yes\nnodir"
    _, out, keys, _ = sh('which exiftool ls; type rm; command -v gzip || echo "no gzip"')
    assert out == "/usr/bin/ls\nrm is /usr/bin/rm\nno gzip" and keys == []
    _, out, keys, _ = sh("ls -l /var/log/app")
    assert keys == [("list", "/var/log/app")] and out.startswith("total 5\n-rw-r--r-- 1 user user       17")


def test_failed_command_redirect_leaves_an_empty_file():
    s, _, keys, _ = sh("ls /home/user/nope > /tmp/listing.txt")
    assert s.files["/tmp/listing.txt"] == "" and keys == [("list", "/home/user/nope"), ("write", "/tmp/listing.txt")]
    _, out, _, _ = sh('echo "a 2>b"; echo x 2>/dev/null')
    assert out == "a 2>b\nx"
