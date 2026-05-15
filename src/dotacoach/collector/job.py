import json
import logging
import time

from dotacoach.db.dao import Database

from .opendota import OpenDotaClient

log = logging.getLogger(__name__)


class CollectJob:
    def __init__(self, client: OpenDotaClient, db: Database):
        self.client = client
        self.db = db

    async def collect_for_account(self, account_id: int, since_ts: int) -> int:
        recent = await self.client.recent_matches(account_id)
        new_count = 0
        for m in recent:
            if m["start_time"] < since_ts:
                continue
            detail = await self.client.match(m["match_id"])
            me = next(
                (
                    p
                    for p in detail.get("players", [])
                    if p.get("account_id") == account_id
                ),
                None,
            )
            if me is None:
                continue
            is_radiant = bool(me.get("isRadiant"))
            win = is_radiant == bool(detail.get("radiant_win"))
            self.db.insert_match(
                match_id=m["match_id"],
                start_time=m["start_time"],
                duration=detail.get("duration", 0),
                hero_id=me["hero_id"],
                is_radiant=is_radiant,
                win=win,
                game_mode=detail.get("game_mode", 0),
                lobby_type=detail.get("lobby_type", 0),
                avg_mmr=detail.get("average_rank"),
                raw_json=json.dumps(detail),
                fetched_at=int(time.time()),
            )
            new_count += 1
        return new_count
