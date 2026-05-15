import json
import time

from dotacoach.analysis.llm_models import Task
from dotacoach.db.dao import Database


class TaskTracker:
    def __init__(self, db: Database):
        self.db = db

    def set_current_tasks(self, week_label: str, tasks: list[Task]) -> None:
        for t in tasks:
            self.db.conn.execute(
                """INSERT INTO tasks
                (week_label, description, metric, target, direction,
                 linked_rule_ids, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    week_label,
                    t.description,
                    t.metric,
                    t.target,
                    t.direction,
                    json.dumps(t.linked_rule_ids),
                    int(time.time()),
                ),
            )
        self.db.conn.commit()

    def get_current_tasks(self) -> list[dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM tasks WHERE completed IS NULL ORDER BY id DESC"
        )
        return [dict(r) for r in cur.fetchall()]

    def finalize_week(
        self, week_label: str, actuals: dict[str, float]
    ) -> list[dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM tasks WHERE week_label = ?", (week_label,)
        )
        results = []
        for row in cur.fetchall():
            metric = row["metric"]
            actual = actuals.get(metric)
            if actual is None:
                completed = None
            elif row["direction"] == ">=":
                completed = actual >= row["target"]
            else:
                completed = actual <= row["target"]
            self.db.conn.execute(
                "UPDATE tasks SET completed = ?, actual = ? WHERE id = ?",
                (
                    1 if completed else 0 if completed is False else None,
                    actual,
                    row["id"],
                ),
            )
            results.append({**dict(row), "completed": completed, "actual": actual})
        self.db.conn.commit()
        return results
