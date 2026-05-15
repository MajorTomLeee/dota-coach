import time
from dotacoach.realtime.game_state import GameStateTracker
from dotacoach.events import Event
from dotacoach.gsi.models import GsiPayload, Player, Hero, Map, Item

def make_payload(gold=1500, has_tp=False, alive=True, level=10, game_time=600):
    items = {}
    if has_tp:
        items["slot0"] = Item(name="item_tpscroll")
    return GsiPayload(
        map=Map(name="start", matchid="1", game_time=game_time, clock_time=game_time-60,
                daytime=True, game_state="DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"),
        player=Player(steamid="1", name="t", activity="playing", gold=gold),
        hero=Hero(id=14, name="npc_dota_hero_pudge", level=level, alive=alive),
    )

def test_tracker_updates_from_gsi_state():
    tracker = GameStateTracker()
    p = make_payload(gold=1000)
    tracker.apply_event(Event(type="gsi.state", payload={"payload": p}))
    ctx = tracker.snapshot()
    assert ctx["player"].gold == 1000
    assert ctx["has_tp"] is False
    assert ctx["game_time"] == 600

def test_enemy_ult_remaining_decrements_over_time(monkeypatch):
    tracker = GameStateTracker()
    now = [1000.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])
    tracker.apply_event(Event(
        type="log.enemy_cast",
        payload={"game_time": 0, "hero": "npc_dota_hero_lion",
                 "ability": "lion_finger_of_death"}
    ))
    now[0] += 50
    ctx = tracker.snapshot()
    rem = ctx["enemy_ults"].get("npc_dota_hero_lion")
    # Lion 大默认 CD ~100s（无 aghs）；过 50s 应剩 ~50s
    assert rem is not None
    assert 40 <= rem <= 60
