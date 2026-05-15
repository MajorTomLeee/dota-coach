from pathlib import Path
from dotacoach.db.dao import Database

def test_init_creates_tables(tmp_path):
    db = Database(tmp_path / "test.db")
    db.init_schema()
    cur = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    names = [r[0] for r in cur.fetchall()]
    assert "matches" in names
    assert "match_events" in names
    assert "tasks" in names
    assert "reports" in names

def test_insert_and_get_match(tmp_path):
    db = Database(tmp_path / "test.db")
    db.init_schema()
    db.insert_match(
        match_id=1, start_time=100, duration=2000, hero_id=14,
        is_radiant=True, win=True, game_mode=22, lobby_type=7,
        avg_mmr=4500, raw_json='{}', fetched_at=1000,
    )
    rows = db.get_matches_since(0)
    assert len(rows) == 1
    assert rows[0]["match_id"] == 1
