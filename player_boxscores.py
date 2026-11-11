"""Rebuild ESPN player box-score statistics from cached Raw_Boxscores.

Usage: python player_boxscores.py [--db espn_cfb_2026.db]
No ESPN requests are made. Run again after the main notebook refreshes raw data.
"""
import argparse
import json
import sqlite3
import zlib

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS Player_Box_Scores (
    game_id TEXT NOT NULL REFERENCES Games(game_id),
    team_id TEXT NOT NULL REFERENCES Teams(team_id),
    player_id TEXT NOT NULL,
    player_name TEXT,
    stat_category TEXT NOT NULL,
    stat_name TEXT NOT NULL,
    stat_label TEXT,
    stat_value REAL,
    display_value TEXT,
    PRIMARY KEY (game_id, team_id, player_id, stat_category, stat_name)
);
CREATE INDEX IF NOT EXISTS idx_player_box_scores_team
    ON Player_Box_Scores(team_id);
CREATE INDEX IF NOT EXISTS idx_player_box_scores_category
    ON Player_Box_Scores(stat_category, stat_name);
"""

INSERT = """
INSERT INTO Player_Box_Scores
(game_id, team_id, player_id, player_name, stat_category, stat_name,
 stat_label, stat_value, display_value)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def numeric_or_none(value):
    """Keep compound ESPN display values as text rather than inventing numbers."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_player_stats(game_id, boxscore):
    """Yield one row per game/team/player/category/statistic."""
    for team_entry in boxscore.get("players", []):
        team_id = (team_entry.get("team") or {}).get("id")
        if team_id is None:
            continue
        for category in team_entry.get("statistics", []):
            category_name = category.get("name")
            if not category_name:
                continue
            keys = category.get("keys") or []
            labels = category.get("labels") or []
            for entry in category.get("athletes", []):
                athlete = entry.get("athlete") or {}
                player_id = athlete.get("id")
                if player_id is None:
                    continue  # No stable player identifier; do not invent one.
                for index, raw_value in enumerate(entry.get("stats") or []):
                    if index >= len(keys) or not keys[index]:
                        continue
                    display = None if raw_value is None else str(raw_value)
                    yield (
                        str(game_id), str(team_id), str(player_id),
                        athlete.get("displayName"), str(category_name), str(keys[index]),
                        labels[index] if index < len(labels) else None,
                        numeric_or_none(raw_value), display,
                    )


def rebuild_from_raw(connection):
    """Atomically rebuild player stats from all cached payloads; no network access."""
    connection.execute("PRAGMA foreign_keys = ON")
    cached = connection.execute(
        "SELECT game_id, payload FROM Raw_Boxscores WHERE payload IS NOT NULL"
    ).fetchall()
    total_rows = 0
    games_with_players = 0
    with connection:
        connection.executescript(CREATE_TABLE)
        # Rebuild rather than upsert: removed/corrected ESPN stats cannot linger.
        connection.execute("DELETE FROM Player_Box_Scores")
        for game_id, blob in cached:
            boxscore = json.loads(zlib.decompress(blob))
            rows = list(parse_player_stats(game_id, boxscore))
            if rows:
                games_with_players += 1
                connection.executemany(INSERT, rows)
                total_rows += len(rows)
    return len(cached), games_with_players, total_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="espn_cfb_2026.db", help="SQLite database path")
    args = parser.parse_args()
    with sqlite3.connect(args.db) as connection:
        cached, games, rows = rebuild_from_raw(connection)
    print(f"Cached payloads: {cached}; games with player stats: {games}; player-stat rows: {rows}")


if __name__ == "__main__":
    main()
