from dotacoach.analysis.llm_models import Task
from dotacoach.db.dao import Database
from dotacoach.tasks.tracker import TaskTracker


def test_save_and_load_current_tasks(tmp_path):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    tracker = TaskTracker(db)
    tracker.set_current_tasks(
        "2026-W20",
        [
            Task(
                description="d",
                metric="vision.wards_per_game",
                target=5,
                direction=">=",
                linked_rule_ids=["enemies_missing"],
            )
        ],
    )
    current = tracker.get_current_tasks()
    assert len(current) == 1
    assert current[0]["metric"] == "vision.wards_per_game"


def test_finalize_marks_completed(tmp_path):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    tracker = TaskTracker(db)
    tracker.set_current_tasks(
        "2026-W20",
        [Task(description="d", metric="m", target=5, direction=">=")],
    )
    results = tracker.finalize_week("2026-W20", actuals={"m": 6.0})
    assert results[0]["completed"] is True
    assert results[0]["actual"] == 6.0
