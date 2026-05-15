import asyncio
from dotacoach.consolelog.tailer import LogTailer
from dotacoach.events import EventBus

async def test_tailer_emits_events_on_append(tmp_path):
    log = tmp_path / "console.log"
    log.write_text("00:00:01 npc_dota_hero_lion cast lion_finger_of_death\n")
    bus = EventBus()
    received = []
    bus.subscribe("log.enemy_cast", lambda e: received.append(e))
    tailer = LogTailer(log, bus)
    task = asyncio.create_task(tailer.run())
    await asyncio.sleep(0.1)
    with log.open("a") as f:
        f.write("00:00:02 npc_dota_hero_pudge died\n")
        f.write("00:00:03 npc_dota_hero_lion cast lion_finger_of_death\n")
    await asyncio.sleep(0.2)
    tailer.stop()
    await task
    assert len(received) >= 1
