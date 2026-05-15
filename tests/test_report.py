from dotacoach.analysis.report import render_markdown
from dotacoach.analysis.llm_models import LlmReport, Pattern, Task


def test_render_basic():
    r = LlmReport(
        patterns=[
            Pattern(title="t1", evidence="e1", hypothesis="h1", verification="v1")
        ],
        tasks=[
            Task(description="d1", metric="vision.wards_per_game",
                 target=5, direction=">=", linked_rule_ids=["enemies_missing"])
        ],
        hero_pool_advice="停打 SF",
    )
    md = render_markdown(
        week_label="2026-W20", report=r,
        previous_task_results=[
            {"description": "上周任务", "target": 3, "direction": ">=",
             "actual": 4, "completed": True}
        ],
    )
    assert "2026-W20" in md
    assert "## 上周任务回顾" in md
    assert "\u2705" in md
    assert "## 本周 3 大 pattern" in md or "## 本周核心 pattern" in md
    assert "t1" in md
    assert "停打 SF" in md
    assert "vision.wards_per_game" in md
