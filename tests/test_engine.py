import time
from dotacoach.realtime.engine import RuleEngine
from dotacoach.realtime.rule import Rule

def make_rule(rid, when, say, priority="tactical", cooldown=30):
    return Rule(id=rid, category="t", priority=priority, cooldown_s=cooldown,
                when=when, say=say)

def test_rule_fires_when_condition_true():
    rule = make_rule("r1", "x > 5", "go")
    engine = RuleEngine([rule])
    out = engine.evaluate({"x": 10})
    assert len(out) == 1
    assert out[0].text == "go"

def test_rule_does_not_fire_when_condition_false():
    rule = make_rule("r1", "x > 5", "go")
    engine = RuleEngine([rule])
    assert engine.evaluate({"x": 1}) == []

def test_cooldown_blocks_repeat(monkeypatch):
    rule = make_rule("r1", "x > 5", "go", cooldown=60)
    engine = RuleEngine([rule])
    now = [1000.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])
    assert engine.evaluate({"x": 10}) != []
    now[0] += 10
    assert engine.evaluate({"x": 10}) == []
    now[0] += 60
    assert engine.evaluate({"x": 10}) != []

def test_priority_ordering():
    high = make_rule("h", "True", "急", priority="critical")
    low  = make_rule("l", "True", "缓", priority="housekeeping")
    engine = RuleEngine([low, high])
    out = engine.evaluate({})
    assert out[0].text == "急"

def test_say_template_substitutes():
    rule = make_rule("r1", "True", "{name} 大快好了")
    engine = RuleEngine([rule])
    out = engine.evaluate({"name": "莱恩"})
    assert out[0].text == "莱恩 大快好了"
