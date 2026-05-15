import httpx
import respx

from dotacoach.collector.opendota import OpenDotaClient


@respx.mock
async def test_get_recent_matches():
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
                    "kills": 5,
                    "deaths": 2,
                    "assists": 8,
                    "lobby_type": 7,
                    "game_mode": 22,
                }
            ],
        )
    )
    client = OpenDotaClient()
    try:
        matches = await client.recent_matches(12345)
        assert len(matches) == 1
        assert matches[0]["match_id"] == 1
    finally:
        await client.close()


@respx.mock
async def test_get_match_detail():
    respx.get("https://api.opendota.com/api/matches/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "match_id": 1,
                "duration": 2000,
                "start_time": 1715800000,
                "players": [],
            },
        )
    )
    client = OpenDotaClient()
    try:
        m = await client.match(1)
        assert m["match_id"] == 1
    finally:
        await client.close()
