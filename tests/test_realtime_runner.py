import asyncio
from pathlib import Path

from dotacoach.events import Event, EventBus
from dotacoach.gsi.models import GsiPayload, Hero, Map, Player
from dotacoach.realtime.runner import RealtimeRunner
from dotacoach.realtime.voice import FakeBackend


async def test_runner_publishes_announcement_on_no_tp(tmp_path):
    bus = EventBus()
    backend = FakeBackend()
    rules_yaml = tmp_path / "rules.yaml"
    rules_yaml.write_text(
        """
rules:
  - id: no_tp
    category: economy
    priority: critical
    cooldown_s: 0
    when: "player and player.gold >= 50 and not has_tp and game_time > 0"
    say: "买 TP"
"""
    )
    runner = RealtimeRunner(bus, rules_yaml, backend)
    await runner.start()
    p = GsiPayload(
        map=Map(
            name="x",
            matchid="1",
            game_time=600,
            clock_time=540,
            daytime=True,
            game_state="DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
        ),
        player=Player(steamid="1", name="t", activity="playing", gold=1000),
        hero=Hero(id=14, name="npc_dota_hero_pudge", level=5, alive=True),
    )
    await bus.publish(Event(type="gsi.state", payload={"payload": p}))
    await asyncio.sleep(0.2)
    await runner.stop()
    assert "买 TP" in backend.played
