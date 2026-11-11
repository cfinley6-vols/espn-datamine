
import sqlite3
import pandas as pd

DB_PATH = "espn_cfb_2026.db"

DEFENSIVE_CATEGORIES = ["defensive", "interceptions"]


def build_team_defensive_stats():
    with sqlite3.connect(DB_PATH) as conn:
        # Read the player-level defensive statistics.
        player_stats = pd.read_sql_query(
            """
            SELECT game_id, team_id, stat_category,
                   stat_name, stat_value
            FROM Player_Box_Scores
            WHERE stat_category IN ('defensive', 'interceptions')
            """,
            conn,
        )

        # Sum numeric statistics for each team in each game.
        # min_count=1 preserves NULL when all values are missing.
        team_stats = (
            player_stats.groupby(
                ["game_id", "team_id", "stat_category", "stat_name"],
                as_index=False,
            )["stat_value"]
            .sum(min_count=1)
        )

        team_stats.rename(
            columns={"stat_value": "team_total"},
            inplace=True,
        )

        # Store the calculated team-level statistics.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Team_Defensive_Stats (
                game_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                stat_category TEXT NOT NULL,
                stat_name TEXT NOT NULL,
                team_total REAL,
                PRIMARY KEY (
                    game_id, team_id, stat_category, stat_name
                )
            )
            """
        )

        # Replace previously calculated results so reruns
        # don't create duplicate records.
        conn.execute("DELETE FROM Team_Defensive_Stats")

        team_stats.to_sql(
            "Team_Defensive_Stats",
            conn,
            if_exists="append",
            index=False,
        )

        print(f"Player-stat rows processed: {len(player_stats):,}")
        print(f"Team-stat rows generated: {len(team_stats):,}")
        print(
            "Games represented:",
            team_stats["game_id"].nunique(),
        )
        print(
            "Teams represented:",
            team_stats["team_id"].nunique(),
        )

        print("\nSample: San Jose State, game 401864494")
        sample = team_stats[
            (team_stats["game_id"].astype(str) == "401864494")
            & (team_stats["team_id"].astype(str) == "23")
        ]

        print(
            sample[
                ["stat_category", "stat_name", "team_total"]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    build_team_defensive_stats()
