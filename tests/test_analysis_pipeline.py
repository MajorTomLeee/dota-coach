import json
import time
from unittest.mock import AsyncMock, MagicMock

from dotacoach.analysis.pipeline import run_weekly_pipeline
from dotacoach.db.dao import Database


async def test_pipeline_produces_report(tmp_path, monkeypatch):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    # 塞两局：1 win + 1 loss
    for i, win in enumerate([True, False]):
        db.insert_match(
            match_id=i,
            start_time=int(time.time()) - 100 * (i + 1),
            duration=2000,
            hero_id=14,
            is_radiant=True,
            win=win,
            game_mode=22,
            lobby_type=7,
            avg_mmr=4500,
            raw_json=json.dumps(
                {
                    "duration": 2000,
                    "radiant_win": win,
                    "players": [
                        {
                            "account_id": 42,
                            "isRadiant": True,
                            "hero_id": 14,
                            "kills": 5,
                            "deaths": 2,
                            "assists": 3,
                            "gold_t": [100 * j for j in range(30)],
                            "xp_t": [150 * j for j in range(30)],
                            "lh_t": [5 * j for j in range(30)],
                            "dn_t": [j for j in range(30)],
                            "purchase_log": [],
                            "gold_per_min": 500,
                            "xp_per_min": 600,
                        }
                    ],
                }
            ),
            fetched_at=int(time.time()),
        )
    fake_resp = MagicMock()
    fake_resp.content = [
        MagicMock(
            text=json.dumps(
                {
                    "patterns": [
                        {
                            "title": "t",
                            "evidence": "e",
                            "hypothesis": "h",
                            "verification": "v",
                        }
                    ],
                    "tasks": [
                        {
                            "description": "d",
                            "metric": "vision.wards_per_game",
                            "target": 5,
                            "direction": ">=",
                            "linked_rule_ids": [],
                        }
                    ],
                    "hero_pool_advice": "ok",
                }
            )
        )
    ]
    fake_client = MagicMock()
    fake_client.messages.create = AsyncMock(return_value=fake_resp)

    md, report = await run_weekly_pipeline(
        db=db,
        account_id=42,
        week_label="2026-W20",
        anthropic_client=fake_client,
        model="claude-opus-4-7",
        since_ts=0,
    )
    assert "2026-W20" in md
    assert "t" in md
