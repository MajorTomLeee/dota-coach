import asyncio
from dotacoach.realtime.voice import Speaker, FakeBackend
from dotacoach.realtime.engine import Announcement

async def test_speaker_plays_via_backend():
    backend = FakeBackend()
    speaker = Speaker(backend)
    await speaker.start()
    await speaker.say(Announcement(rule_id="r", text="买 TP", priority="critical"))
    await asyncio.sleep(0.05)
    await speaker.stop()
    assert backend.played == ["买 TP"]

async def test_critical_interrupts_low():
    backend = FakeBackend(speak_delay=0.2)
    speaker = Speaker(backend)
    await speaker.start()
    await speaker.say(Announcement(rule_id="a", text="缓", priority="housekeeping"))
    await asyncio.sleep(0.05)
    await speaker.say(Announcement(rule_id="b", text="急", priority="critical"))
    await asyncio.sleep(0.5)
    await speaker.stop()
    assert "急" in backend.played
    # 低优可能被打断或丢弃，重点是 critical 一定播放
