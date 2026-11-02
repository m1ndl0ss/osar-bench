"""Sample-size arithmetic in osar.plan."""
import pandas as pd

from osar.plan import n_per_cell, task_rates

TASKS = [f"T{i}" for i in range(1, 12)]


def test_worst_case_with_eleven_tasks():
    rates = {t: (0.5, 0.5) for t in TASKS}
    assert n_per_cell(rates, 0.10, "one-sided") == 29
    assert n_per_cell(rates, 0.10, "two-sided") == 36


def test_lower_rates_need_fewer_rollouts_and_zero_variance_floors_at_one():
    assert n_per_cell({t: (0.1, 0.2) for t in TASKS}, 0.10, "one-sided") < 29
    assert n_per_cell({t: (0.0, 0.0) for t in TASKS}, 0.10, "one-sided") == 1


def test_missing_tasks_fall_back_to_half():
    rol = pd.DataFrame({"task_id": ["T1", "T1", "T1"], "framing": ["tight", "tight", "loose"],
                        "any_oos": [True, False, True]})
    rates = task_rates(rol, TASKS, "any_oos")
    assert rates["T1"] == (0.5, 1.0)
    assert rates["T2"] == (0.5, 0.5)
    assert task_rates(pd.DataFrame(), TASKS, "any_oos")["T1"] == (0.5, 0.5)
