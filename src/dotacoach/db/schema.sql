CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    start_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    hero_id INTEGER NOT NULL,
    is_radiant INTEGER NOT NULL,
    win INTEGER NOT NULL,
    game_mode INTEGER NOT NULL,
    lobby_type INTEGER NOT NULL,
    avg_mmr INTEGER,
    raw_json TEXT NOT NULL,
    fetched_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_matches_start ON matches(start_time);

CREATE TABLE IF NOT EXISTS match_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    time_s INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    x INTEGER,
    y INTEGER,
    payload_json TEXT,
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

CREATE INDEX IF NOT EXISTS idx_events_match_time ON match_events(match_id, time_s);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_label TEXT NOT NULL,
    description TEXT NOT NULL,
    metric TEXT NOT NULL,
    target REAL NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('>=', '<=')),
    linked_rule_ids TEXT,
    created_at INTEGER NOT NULL,
    completed INTEGER,
    actual REAL
);

CREATE INDEX IF NOT EXISTS idx_tasks_week ON tasks(week_label);

CREATE TABLE IF NOT EXISTS reports (
    week_label TEXT PRIMARY KEY,
    generated_at INTEGER NOT NULL,
    markdown TEXT NOT NULL
);
