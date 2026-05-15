import json
from dataclasses import dataclass

from dotacoach.db.dao import Database


@dataclass
class MatchRecord:
    match_id: int
    hero_id: int
    win: bool
    duration: int
    player: dict   # 该账号在这局里的 player 数据（OpenDota player obj）


def load_split(db: Database, account_id: int, since_ts: int
               ) -> tuple[list[MatchRecord], list[MatchRecord]]:
    rows = db.get_matches_since(since_ts)
    wins: list[MatchRecord] = []
    losses: list[MatchRecord] = []
    for r in rows:
        raw = json.loads(r["raw_json"])
        me = next((p for p in raw.get("players", [])
                   if p.get("account_id") == account_id), None)
        if me is None:
            continue
        rec = MatchRecord(
            match_id=r["match_id"], hero_id=r["hero_id"], win=bool(r["win"]),
            duration=r["duration"], player=me,
        )
        (wins if rec.win else losses).append(rec)
    return wins, losses
