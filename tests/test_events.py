import asyncio
from dotacoach.events import EventBus, Event

async def test_pub_sub():
    bus = EventBus()
    received = []
    async def handler(e: Event):
        received.append(e)
    bus.subscribe("test", handler)
    await bus.publish(Event(type="test", payload={"x": 1}))
    await asyncio.sleep(0.01)
    assert len(received) == 1
    assert received[0].payload["x"] == 1

async def test_multiple_subscribers():
    bus = EventBus()
    a, b = [], []
    bus.subscribe("e", lambda e: a.append(e))
    bus.subscribe("e", lambda e: b.append(e))
    await bus.publish(Event(type="e", payload={}))
    await asyncio.sleep(0.01)
    assert len(a) == 1 and len(b) == 1
