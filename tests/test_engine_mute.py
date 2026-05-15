from dotacoach.realtime.engine import RuleEngine
from dotacoach.realtime.rule import Rule

def make(rid, prio="tactical"):
    return Rule(id=rid, category="t", priority=prio, cooldown_s=0,
                when="True", say="x")

def test_global_mute_blocks_all():
    engine = RuleEngine([make("r1")])
    engine.set_muted(True)
    assert engine.evaluate({}) == []
    engine.set_muted(False)
    assert engine.evaluate({}) != []

def test_combat_silence_blocks_non_critical():
    engine = RuleEngine([make("low", "tactical"), make("high", "critical")])
    engine.set_in_combat(True)
    out = engine.evaluate({})
    ids = [a.rule_id for a in out]
    assert "low" not in ids
    assert "high" in ids
