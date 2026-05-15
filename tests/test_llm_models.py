from dotacoach.analysis.llm_models import LlmReport, Pattern, Task


def test_parse_valid():
    payload = {
        "patterns": [
            {"title": "劣势期决策过激",
             "evidence": "输局 75% 在劣势开团",
             "hypothesis": "把还能打=应该打",
             "verification": "开团前 ping 队友"}
        ],
        "tasks": [
            {"description": "5 局劣势期开团前 ping",
             "metric": "tasks.ping_before_dive",
             "target": 5, "direction": ">=",
             "linked_rule_ids": ["level_disadvantage"]}
        ],
        "hero_pool_advice": "停打 SF，回归 PA"
    }
    r = LlmReport.model_validate(payload)
    assert len(r.patterns) == 1
    assert r.tasks[0].target == 5
