import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA_FILE = Path(__file__).parent / "schema.sql"

class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA_FILE.read_text())
        self.conn.commit()

    def insert_match(self, **kwargs) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO matches
            (match_id, start_time, duration, hero_id, is_radiant, win,
             game_mode, lobby_type, avg_mmr, raw_json, fetched_at)
            VALUES (:match_id, :start_time, :duration, :hero_id, :is_radiant,
                    :win, :game_mode, :lobby_type, :avg_mmr, :raw_json, :fetched_at)""",
            kwargs,
        )
        self.conn.commit()

    def insert_events(self, match_id: int, events: Iterable[dict]) -> None:
        self.conn.executemany(
            """INSERT INTO match_events
            (match_id, time_s, event_type, x, y, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (match_id, e["time_s"], e["event_type"],
                 e.get("x"), e.get("y"), e.get("payload_json"))
                for e in events
            ],
        )
        self.conn.commit()

    def get_matches_since(self, since_ts: int) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT * FROM matches WHERE start_time >= ? ORDER BY start_time",
            (since_ts,),
        )
        return cur.fetchall()
