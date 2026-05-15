from dotacoach.events import EventBus
from dotacoach.realtime.runner import RealtimeRunner
from dotacoach.realtime.voice import FakeBackend


async def test_runner_accepts_task_list(tmp_path):
    rules_yaml = tmp_path / "rules.yaml"
    rules_yaml.write_text(
        """
rules:
  - id: r_a
    category: c
    priority: tactical
    cooldown_s: 30
    when: "True"
    say: "x"
"""
    )
    bus = EventBus()
    runner = RealtimeRunner(
        bus,
        rules_yaml,
        FakeBackend(),
        current_tasks=[
            {
                "linked_rule_ids": '["r_a"]',
                "description": "d",
                "metric": "m",
                "target": 1,
                "direction": ">=",
            }
        ],
    )
    assert runner.engine.rules[0].priority == "critical"
    assert runner.engine.rules[0].cooldown_s == 15
