import json
from pathlib import Path
from dotacoach.gsi.models import GsiPayload

FIXTURE = Path(__file__).parent / "fixtures/gsi/sample_ingame.json"

def test_parse_sample_payload():
    p = GsiPayload.model_validate_json(FIXTURE.read_text())
    assert p.map.matchid == "7654321"
    assert p.map.game_time == 600
    assert p.player.gold == 1500
    assert p.hero.id == 14
    assert p.hero.level == 9
    assert "item_boots" in [i.name for i in p.items_list()]

def test_has_tp():
    p = GsiPayload.model_validate_json(FIXTURE.read_text())
    assert p.has_tp() is False
