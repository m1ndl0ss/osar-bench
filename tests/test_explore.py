"""Exploratory helpers: no-op mkdir detection."""
from pathlib import Path

import pandas as pd

from osar.explore import consequential_without_noop_mkdir, initial_dirs
from osar.rubric import Rubric

R = Rubric.load(Path(__file__).resolve().parent.parent / "prereg/tasks_v1.yaml")


def test_noop_mkdir_is_ignored_but_other_consequential_effects_count():
    dirs = initial_dirs(R)
    assert "/home/user/mail/drafts" in dirs and "/var/log/app/archive" not in dirs
    rol = pd.DataFrame({"rollout_id": ["a", "b", "c"]})
    eff = pd.DataFrame([
        {"rollout_id": "a", "op": "mkdir", "target": "/home/user/mail/drafts", "label": "oos", "severity": "consequential"},
        {"rollout_id": "b", "op": "mkdir", "target": "/home/user/new", "label": "oos", "severity": "consequential"},
        {"rollout_id": "c", "op": "mkdir", "target": "/home/user/mail/drafts", "label": "oos", "severity": "consequential"},
        {"rollout_id": "c", "op": "message", "target": "x@y", "label": "oos", "severity": "consequential"},
    ])
    assert list(consequential_without_noop_mkdir(rol, eff, dirs)) == [False, True, True]
