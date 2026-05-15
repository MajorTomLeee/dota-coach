from dotacoach.realtime.rule import Rule
from dotacoach.tasks.linker import boost_rules_for_tasks


def test_boost_lowers_cooldown_for_linked_rules():
    rules = [
        Rule(
            id="enemies_missing",
            category="m",
            priority="tactical",
            cooldown_s=20,
            when="True",
            say="x",
        ),
        Rule(
            id="other",
            category="o",
            priority="tactical",
            cooldown_s=30,
            when="True",
            say="y",
        ),
    ]
    tasks = [
        {
            "linked_rule_ids": '["enemies_missing"]',
            "description": "d",
            "metric": "m",
            "target": 5,
            "direction": ">=",
        }
    ]
    out = boost_rules_for_tasks(rules, tasks)
    by_id = {r.id: r for r in out}
    # linked rule 优先级提升 + 冷却减半
    assert by_id["enemies_missing"].priority == "critical"
    assert by_id["enemies_missing"].cooldown_s == 10
    assert by_id["other"].priority == "tactical"
    assert by_id["other"].cooldown_s == 30
