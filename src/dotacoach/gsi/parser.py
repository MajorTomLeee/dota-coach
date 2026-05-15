from typing import Optional
from dotacoach.events import Event
from .models import GsiPayload

def diff_to_events(prev: Optional[GsiPayload], curr: GsiPayload) -> list[Event]:
    out: list[Event] = []
    if not curr.in_game():
        return out

    out.append(Event(type="gsi.state", payload={"payload": curr}))

    if curr.player and curr.player.gold >= 50 and not curr.has_tp():
        out.append(Event(
            type="gsi.no_tp",
            payload={"gold": curr.player.gold, "game_time": curr.map.game_time}
        ))

    if (
        prev and prev.hero and curr.hero
        and prev.hero.buyback_cooldown > 0 and curr.hero.buyback_cooldown == 0
        and curr.hero.alive
    ):
        out.append(Event(
            type="gsi.buyback_ready",
            payload={"game_time": curr.map.game_time}
        ))

    if (
        prev and prev.hero and curr.hero
        and prev.hero.alive and not curr.hero.alive
    ):
        out.append(Event(
            type="gsi.death",
            payload={
                "game_time": curr.map.game_time,
                "respawn_seconds": curr.hero.respawn_seconds,
                "x": curr.hero.xpos, "y": curr.hero.ypos,
            }
        ))

    return out
