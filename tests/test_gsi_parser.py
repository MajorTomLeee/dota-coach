import json
from pathlib import Path
from dotacoach.gsi.models import GsiPayload
from dotacoach.gsi.parser import diff_to_events

FIXTURE = Path(__file__).parent / "fixtures/gsi/sample_ingame.json"

async def test_first_payload_emits_state_event():
    payload = GsiPayload.model_validate_json(FIXTURE.read_text())
    events = diff_to_events(prev=None, curr=payload)
    types = [e.type for e in events]
    assert "gsi.state" in types

async def test_no_tp_emits_event():
    payload = GsiPayload.model_validate_json(FIXTURE.read_text())
    events = diff_to_events(prev=None, curr=payload)
    types = [e.type for e in events]
    assert "gsi.no_tp" in types

async def test_buyback_ready_event_when_cooldown_hits_zero():
    a = GsiPayload.model_validate_json(FIXTURE.read_text())
    b = GsiPayload.model_validate_json(FIXTURE.read_text())
    a.hero.buyback_cooldown = 5
    b.hero.buyback_cooldown = 0
    events = diff_to_events(prev=a, curr=b)
    assert any(e.type == "gsi.buyback_ready" for e in events)
