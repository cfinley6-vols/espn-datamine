#!/usr/bin/env python3
"""Export one season defensive summary row per FBS team.

This reads the derived tables built by the current ``cfb2026.ipynb`` pipeline.
It does not fetch ESPN data, modify SQLite, or require Jupyter to run.

Usage:
    python3 season_defensive_rollups.py
    python3 season_defensive_rollups.py --db path/to/espn_cfb_2026.db
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from pathlib import Path

import pandas as pd


DEFAULT_DB = "espn_cfb_2026.db"
DEFAULT_OUTPUT = "team_defensive_season_2026.csv"

# These values are ratios or compound text and must not be summed as ordinary
# per-game numbers. They are recomputed from season-long numerators/denominators.
SPECIAL_OPPONENT_STATS = {
    "offensePointsAllowed",
    "yardsPerPassAllowed",
    "yardsPerRushAllowed",
    "thirdDownEffAllowed",
    "fourthDownEffAllowed",
    "completionsAttemptsAllowed",
    "opponentPossessionTime",
    "opponentPenaltiesYards",
}

SPOT_CHECK_IDS = ("2633", "333", "23")  # Tennessee, Alabama, San Jose State


def validate_database(conn: sqlite3.Connection) -> None:
    required = {
        "Teams",
        "Games",
        "Team_Defensive_Stats",
        "Team_Defense_Opponent_Stats",
    }
    present = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    missing = sorted(required - present)
    if missing:
        raise SystemExit(
            "Database is missing required tables: "
            + ", ".join(missing)
            + ". Run the current data pipeline before creating the rollup."
        )


def load_fbs_teams(conn: sqlite3.Connection) -> pd.DataFrame:
    teams = pd.read_sql_query(
        """
        SELECT team_id, display_name AS team_name, conference
        FROM Teams
        WHERE conference IS NOT NULL AND conference != ''
        ORDER BY display_name
        """,
        conn,
    )
    teams["team_id"] = teams["team_id"].astype("string")
    return teams


def load_games_played(conn: sqlite3.Connection) -> pd.DataFrame:
    games = pd.read_sql_query(
        """
        SELECT team_id, COUNT(DISTINCT game_id) AS games_played
        FROM (
            SELECT game_id, home_team_id AS team_id
            FROM Games WHERE status = 'Final'
            UNION ALL
            SELECT game_id, away_team_id AS team_id
            FROM Games WHERE status = 'Final'
        )
        GROUP BY team_id
        """,
        conn,
    )
    games["team_id"] = games["team_id"].astype("string")
    return games


def add_total_and_average(
    season: pd.DataFrame,
    values: pd.Series,
    name: str,
) -> pd.DataFrame:
    total_column = f"{name}_total"
    average_column = f"{name}_per_game"
    totals = values.rename(total_column).reset_index()
    totals["team_id"] = totals["team_id"].astype("string")
    season = season.merge(totals, on="team_id", how="left")
    season[total_column] = season[total_column].fillna(0)
    season[average_column] = season[total_column].div(
        season["games_played"].replace(0, pd.NA)
    )
    return season


def parse_pair(
    opponent_rows: pd.DataFrame,
    stat_name: str,
    separator: str,
) -> pd.DataFrame:
    """Parse ESPN compound values such as ``7-15`` or ``18/29``."""
    rows = opponent_rows[opponent_rows["stat_name"] == stat_name].copy()
    escaped = r"\/" if separator == "/" else separator
    parsed = rows["display_value"].astype("string").str.extract(
        rf"^\s*(\d+)\s*{escaped}\s*(\d+)\s*$"
    )
    rows["made"] = pd.to_numeric(parsed[0], errors="coerce")
    rows["attempted"] = pd.to_numeric(parsed[1], errors="coerce")
    return rows


def safe_percentage(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.replace(0, pd.NA)).mul(100)


def create_season_rollup(conn: sqlite3.Connection) -> pd.DataFrame:
    """Build the issue #11 one-row-per-FBS-team season table."""
    season = load_fbs_teams(conn).merge(
        load_games_played(conn), on="team_id", how="left"
    )
    season["games_played"] = season["games_played"].fillna(0).astype(int)
    fbs_ids = set(season["team_id"])

    opponent = pd.read_sql_query(
        """
        SELECT game_id, team_id, opponent_id, stat_name, stat_value, display_value
        FROM Team_Defense_Opponent_Stats
        """,
        conn,
    )
    opponent["team_id"] = opponent["team_id"].astype("string")
    opponent = opponent[opponent["team_id"].isin(fbs_ids)].copy()
    opponent["stat_value"] = pd.to_numeric(
        opponent["stat_value"], errors="coerce"
    )

    # Ordinary numeric stats: sum first, then divide by all games played.
    direct = opponent[
        opponent["stat_value"].notna()
        & ~opponent["stat_name"].isin(SPECIAL_OPPONENT_STATS)
    ]
    for stat_name, rows in direct.groupby("stat_name", sort=True):
        season = add_total_and_average(
            season,
            rows.groupby("team_id")["stat_value"].sum(min_count=1),
            stat_name,
        )

    # Count only points scored by the opposing offense when play-by-play exists;
    # fall back to all points for a game whose play-by-play could not be used.
    points = opponent[
        opponent["stat_name"].isin(["pointsAllowed", "offensePointsAllowed"])
    ].pivot_table(
        index=["game_id", "team_id"],
        columns="stat_name",
        values="stat_value",
        aggfunc="max",
    )
    all_points = points.get("pointsAllowed", pd.Series(index=points.index, dtype=float))
    offense_points = points.get(
        "offensePointsAllowed", pd.Series(index=points.index, dtype=float)
    ).fillna(all_points)
    season = add_total_and_average(
        season,
        offense_points.groupby("team_id").sum(min_count=1),
        "offensePointsAllowed",
    )

    # Completion, third-down and fourth-down percentages use season totals.
    compound_specs = [
        (
            "completionsAttemptsAllowed",
            "/",
            "completionsAllowed",
            "passAttemptsFaced",
            "opponentCompletionPct",
        ),
        (
            "thirdDownEffAllowed",
            "-",
            "thirdDownConversionsAllowed",
            "thirdDownAttemptsFaced",
            "thirdDownPctAllowed",
        ),
        (
            "fourthDownEffAllowed",
            "-",
            "fourthDownConversionsAllowed",
            "fourthDownAttemptsFaced",
            "fourthDownPctAllowed",
        ),
    ]
    for source, separator, made_name, attempted_name, percentage_name in compound_specs:
        parsed = parse_pair(opponent, source, separator)
        made = parsed.groupby("team_id")["made"].sum(min_count=1)
        attempted = parsed.groupby("team_id")["attempted"].sum(min_count=1)
        season = add_total_and_average(season, made, made_name)
        season = add_total_and_average(season, attempted, attempted_name)
        season[percentage_name] = safe_percentage(
            season[f"{made_name}_total"], season[f"{attempted_name}_total"]
        )

    # Recompute yards per attempt from season totals, not per-game averages.
    season["yardsPerPassAllowed"] = season["passingYardsAllowed_total"].div(
        season["passAttemptsFaced_total"].replace(0, pd.NA)
    )
    season["yardsPerRushAllowed"] = season["rushingYardsAllowed_total"].div(
        season["rushingAttemptsFaced_total"].replace(0, pd.NA)
    )

    # ESPN stores possession as MM:SS.
    possession = opponent[opponent["stat_name"] == "opponentPossessionTime"].copy()
    clock = possession["display_value"].astype("string").str.extract(
        r"^\s*(\d+):(\d+)\s*$"
    )
    possession["seconds"] = (
        pd.to_numeric(clock[0], errors="coerce") * 60
        + pd.to_numeric(clock[1], errors="coerce")
    )
    season = add_total_and_average(
        season,
        possession.groupby("team_id")["seconds"].sum(min_count=1),
        "opponentPossessionSeconds",
    )

    # ESPN stores penalties as COUNT-YARDS.
    penalties = parse_pair(opponent, "opponentPenaltiesYards", "-")
    season = add_total_and_average(
        season,
        penalties.groupby("team_id")["made"].sum(min_count=1),
        "opponentPenalties",
    )
    season = add_total_and_average(
        season,
        penalties.groupby("team_id")["attempted"].sum(min_count=1),
        "opponentPenaltyYards",
    )

    # Player box-score defensive stats are already summed per game and team.
    player = pd.read_sql_query(
        """
        SELECT team_id, stat_name, team_total
        FROM Team_Defensive_Stats
        """,
        conn,
    )
    player["team_id"] = player["team_id"].astype("string")
    player = player[player["team_id"].isin(fbs_ids)].copy()
    player["team_total"] = pd.to_numeric(player["team_total"], errors="coerce")
    for stat_name, rows in player.groupby("stat_name", sort=True):
        season = add_total_and_average(
            season,
            rows.groupby("team_id")["team_total"].sum(min_count=1),
            f"player_{stat_name}",
        )

    return season.sort_values("team_name").reset_index(drop=True)


def assert_close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9):
        raise AssertionError(f"{label}: expected {expected}, found {actual}")


def spot_check(conn: sqlite3.Connection, season: pd.DataFrame) -> None:
    """Compare several exported rows directly with the underlying game rows."""
    checked = 0
    for team_id in SPOT_CHECK_IDS:
        match = season[season["team_id"] == team_id]
        if match.empty:
            continue
        row = match.iloc[0]
        games = conn.execute(
            """
            SELECT COUNT(*) FROM Games
            WHERE status = 'Final' AND ? IN (home_team_id, away_team_id)
            """,
            (team_id,),
        ).fetchone()[0]
        points, yards = conn.execute(
            """
            SELECT
                SUM(CASE WHEN stat_name = 'pointsAllowed' THEN stat_value END),
                SUM(CASE WHEN stat_name = 'totalYardsAllowed' THEN stat_value END)
            FROM Team_Defense_Opponent_Stats
            WHERE team_id = ?
            """,
            (team_id,),
        ).fetchone()
        sacks = conn.execute(
            """
            SELECT COALESCE(SUM(team_total), 0)
            FROM Team_Defensive_Stats
            WHERE team_id = ? AND stat_name = 'sacks'
            """,
            (team_id,),
        ).fetchone()[0]
        if int(row["games_played"]) != games:
            raise AssertionError(f"{row['team_name']} games do not match")
        assert_close(row["pointsAllowed_total"], points, "pointsAllowed_total")
        assert_close(row["totalYardsAllowed_total"], yards, "totalYardsAllowed_total")
        assert_close(row["player_sacks_total"], sacks, "player_sacks_total")
        checked += 1
        print(f"Spot check passed: {row['team_name']} ({games} games)")
    if checked == 0:
        raise AssertionError("None of the requested spot-check teams were available")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB, help="Input SQLite database")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output CSV")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.is_file():
        raise SystemExit(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        validate_database(conn)
        season = create_season_rollup(conn)
        spot_check(conn, season)

    output = Path(args.output)
    season.to_csv(output, index=False, float_format="%.4f")
    print(f"Exported {len(season)} FBS team rows to {output.resolve()}")


if __name__ == "__main__":
    main()
