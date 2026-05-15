import json
from dotacoach.analysis.loader import load_split
from dotacoach.db.dao import Database


def test_split_by_win(tmp_path):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    for i, win in enumerate([True, False, True]):
        db.insert_match(
            match_id=i, start_time=1000 + i, duration=2000, hero_id=14,
            is_radiant=True, win=win, game_mode=22, lobby_type=7,
            avg_mmr=4500,
            raw_json=json.dumps({
                "players": [{"account_id": 1, "isRadiant": True,
                             "gold_t": [0, 100, 200], "xp_t": [0, 150, 300],
                             "lh_t": [0, 5, 10], "dn_t": [0, 1, 2],
                             "kills": 5, "deaths": 2, "assists": 3,
                             "purchase_log": []}],
                "duration": 2000,
            }),
            fetched_at=1000,
        )
    wins, losses = load_split(db, account_id=1, since_ts=0)
    assert len(wins) == 2 and len(losses) == 1
