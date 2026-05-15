from pathlib import Path
from dotacoach.realtime.rules_loader import load_rules

def test_load_rules(tmp_path):
    cfg = tmp_path / "rules.yaml"
    cfg.write_text("""
rules:
  - id: no_tp
    category: economy
    priority: critical
    cooldown_s: 60
    when: "player.gold >= 50 and not has_tp"
    say: "买 TP"
  - id: minimap_neglect
    category: map_awareness
    priority: tactical
    cooldown_s: 30
    when: "now - last_minimap_view_ts > 60"
    say: "看小地图"
""")
    rules = load_rules(cfg)
    assert len(rules) == 2
    assert rules[0].id == "no_tp"
    assert rules[0].priority == "critical"
    assert rules[1].cooldown_s == 30
