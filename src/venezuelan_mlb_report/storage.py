from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mlb_id INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('batter', 'pitcher')),
    team TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    birth_country TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS player_seasons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('batter', 'pitcher')),
    stats_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season),
    FOREIGN KEY(player_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS player_daily_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    game_date TEXT NOT NULL,
    opponent TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('batter', 'pitcher')),
    stat_line_json TEXT NOT NULL,
    commentary TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, game_date),
    FOREIGN KEY(player_id) REFERENCES players(id)
);

CREATE TABLE IF NOT EXISTS report_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date TEXT NOT NULL UNIQUE,
    report_body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_latest_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mlb_id INTEGER,
    seed_name TEXT NOT NULL,
    season INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('batter', 'pitcher')),
    subrole TEXT,
    team_seed TEXT,
    team_api TEXT,
    tracking_tier TEXT NOT NULL,
    must_track INTEGER NOT NULL DEFAULT 0,
    selected_for_daily_report INTEGER NOT NULL DEFAULT 0,
    selection_reason TEXT NOT NULL,
    stats_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(seed_name, season)
);

CREATE TABLE IF NOT EXISTS player_historical_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mlb_id INTEGER,
    seed_name TEXT NOT NULL,
    season INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('batter', 'pitcher')),
    subrole TEXT,
    team_api TEXT,
    tracking_tier TEXT NOT NULL,
    must_track INTEGER NOT NULL DEFAULT 0,
    stats_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(seed_name, season)
);
"""


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
