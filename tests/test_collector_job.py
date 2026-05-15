import httpx
import respx

from dotacoach.collector.job import CollectJob
from dotacoach.collector.opendota import OpenDotaClient
from dotacoach.db.dao import Database


@respx.mock
async def test_collect_persists_matches(tmp_path):
    respx.get("https://api.opendota.com/api/players/12345/recentMatches").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "match_id": 1,
                    "hero_id": 14,
                    "start_time": 1715800000,
                    "duration": 2000,
                    "player_slot": 1,
                    "radiant_win": True,
                    "lobby_type": 7,
                    "game_mode": 22,
                    "kills": 5,
                    "deaths": 2,
                    "assists": 8,
                }
            ],
        )
    )
    respx.get("https://api.opendota.com/api/matches/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "match_id": 1,
                "duration": 2000,
                "start_time": 1715800000,
                "radiant_win": True,
                "lobby_type": 7,
                "game_mode": 22,
                "players": [
                    {
                        "account_id": 12345,
                        "hero_id": 14,
                        "isRadiant": True,
                        "kills": 5,
                        "deaths": 2,
                        "assists": 8,
                        "gold_t": [0, 100, 200, 300],
                        "xp_t": [0, 150, 300, 450],
                        "lh_t": [0, 5, 10, 15],
                        "dn_t": [0, 1, 2, 3],
                    }
                ],
            },
        )
    )
    db = Database(tmp_path / "test.db")
    db.init_schema()
    client = OpenDotaClient()
    try:
        job = CollectJob(client, db)
        n = await job.collect_for_account(12345, since_ts=0)
        assert n == 1
        rows = db.get_matches_since(0)
        assert len(rows) == 1
        assert rows[0]["hero_id"] == 14
    finally:
        await client.close()
