import json
from pathlib import Path
from fastapi.testclient import TestClient
from dotacoach.gsi.server import build_app
from dotacoach.events import EventBus

FIXTURE = Path(__file__).parent / "fixtures/gsi/sample_ingame.json"

def test_post_payload_publishes_events():
    bus = EventBus()
    received = []
    bus.subscribe("gsi.state", lambda e: received.append(e))
    app = build_app(bus)
    client = TestClient(app)
    r = client.post("/gsi", json=json.loads(FIXTURE.read_text()))
    assert r.status_code == 200
    import asyncio; asyncio.run(asyncio.sleep(0.05))
    assert len(received) >= 1

def test_post_invalid_payload_returns_200():
    bus = EventBus()
    app = build_app(bus)
    client = TestClient(app)
    r = client.post("/gsi", json={"junk": True})
    # Valve 可能发不完整 payload，server 必须不挂
    assert r.status_code == 200
