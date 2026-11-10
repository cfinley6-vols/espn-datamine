#!/usr/bin/env python3
"""Map and flatten ESPN college-football play-by-play JSON.

This script uses only Python's standard library. By default it inspects the
2026 Alabama at Tennessee game used elsewhere in this repository.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


SUMMARY_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/"
    "college-football/summary?event={event_id}"
)


def fetch_game(event_id: str) -> tuple[dict[str, Any], str]:
    """Download one ESPN game-summary payload."""
    url = SUMMARY_URL.format(event_id=event_id)
    try:
        result = subprocess.run(
            ["curl", "--fail", "--silent", "--show-error", url],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as error:
        raise SystemExit("This script requires curl, which is included with macOS.") from error
    except subprocess.TimeoutExpired as error:
        raise SystemExit("The ESPN request timed out after 30 seconds.") from error

    if result.returncode != 0:
        message = result.stderr.strip() or "unknown curl error"
        raise SystemExit(f"Could not download ESPN game {event_id}: {message}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit("ESPN returned a response that was not valid JSON.") from error

    return payload, url


def collect_drives(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect drive objects from completed or live-game drive buckets."""
    drives_container = payload.get("drives", {})
    drives: list[dict[str, Any]] = []

    if isinstance(drives_container, list):
        return [drive for drive in drives_container if isinstance(drive, dict)]

    if not isinstance(drives_container, dict):
        return drives

    for value in drives_container.values():
        if isinstance(value, list):
            drives.extend(drive for drive in value if isinstance(drive, dict))
        elif isinstance(value, dict) and "plays" in value:
            drives.append(value)

    # A live API response could repeat the current drive in another bucket.
    unique_drives: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for drive in drives:
        drive_id = str(drive.get("id", ""))
        if drive_id and drive_id in seen_ids:
            continue
        if drive_id:
            seen_ids.add(drive_id)
        unique_drives.append(drive)

    return unique_drives


def json_type(value: Any) -> str:
    """Return a JSON-style type name rather than a Python type name."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def walk_json(
    value: Any,
    path: str,
    discovered: dict[str, set[str]],
    examples: dict[str, Any],
    paths_in_play: set[str],
) -> None:
    """Recursively visit every object, array, and value below one play."""
    if path:
        discovered[path].add(json_type(value))
        paths_in_play.add(path)
        if path not in examples and value is not None and not isinstance(value, (dict, list)):
            examples[path] = value

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            walk_json(child, child_path, discovered, examples, paths_in_play)
    elif isinstance(value, list):
        for child in value:
            walk_json(child, f"{path}[]", discovered, examples, paths_in_play)


def build_schema(plays: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build one schema row for every JSON path found in any play."""
    discovered: dict[str, set[str]] = defaultdict(set)
    examples: dict[str, Any] = {}
    plays_present: dict[str, int] = defaultdict(int)

    for play in plays:
        paths_in_play: set[str] = set()
        walk_json(play, "", discovered, examples, paths_in_play)
        for path in paths_in_play:
            plays_present[path] += 1

    return [
        {
            "json_path": path,
            "json_types": "|".join(sorted(discovered[path])),
            "plays_present": plays_present[path],
            "total_plays": len(plays),
            "example_value": examples.get(path, ""),
        }
        for path in sorted(discovered)
    ]


def nested_get(value: dict[str, Any], *keys: str) -> Any:
    """Safely retrieve a value several object levels deep."""
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def flatten_plays(event_id: str, drives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a practical one-row-per-play table for future extraction."""
    rows: list[dict[str, Any]] = []

    for drive_number, drive in enumerate(drives, start=1):
        for play_number, play in enumerate(drive.get("plays", []), start=1):
            if not isinstance(play, dict):
                continue
            rows.append(
                {
                    "game_id": event_id,
                    "drive_number": drive_number,
                    "drive_id": drive.get("id"),
                    "drive_team_id": nested_get(drive, "team", "id"),
                    "drive_team_name": nested_get(drive, "team", "displayName"),
                    "drive_result": drive.get("result"),
                    "drive_description": drive.get("description"),
                    "play_number_in_drive": play_number,
                    "play_id": play.get("id"),
                    "sequence_number": play.get("sequenceNumber"),
                    "period": nested_get(play, "period", "number"),
                    "clock": nested_get(play, "clock", "displayValue"),
                    "play_type_id": nested_get(play, "type", "id"),
                    "play_type_text": nested_get(play, "type", "text"),
                    "play_type_abbreviation": nested_get(play, "type", "abbreviation"),
                    "text": play.get("text"),
                    "start_down": nested_get(play, "start", "down"),
                    "start_distance": nested_get(play, "start", "distance"),
                    "start_yard_line": nested_get(play, "start", "yardLine"),
                    "start_yards_to_endzone": nested_get(play, "start", "yardsToEndzone"),
                    "start_team_id": nested_get(play, "start", "team", "id"),
                    "end_down": nested_get(play, "end", "down"),
                    "end_distance": nested_get(play, "end", "distance"),
                    "end_yard_line": nested_get(play, "end", "yardLine"),
                    "end_yards_to_endzone": nested_get(play, "end", "yardsToEndzone"),
                    "end_team_id": nested_get(play, "end", "team", "id"),
                    "stat_yardage": play.get("statYardage"),
                    "home_score": play.get("homeScore"),
                    "away_score": play.get("awayScore"),
                    "scoring_play": play.get("scoringPlay"),
                    "is_penalty": play.get("isPenalty"),
                    "is_turnover": play.get("isTurnover"),
                    "wallclock": play.get("wallclock"),
                    "modified": play.get("modified"),
                }
            )

    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dictionaries to CSV with stable UTF-8 output."""
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    event_id: str,
    url: str,
    drives: list[dict[str, Any]],
    plays: list[dict[str, Any]],
    schema: list[dict[str, Any]],
    scoring_plays: int,
) -> None:
    """Create a short human-readable record of the discovery."""
    direct_drive_keys = sorted({key for drive in drives for key in drive})
    direct_play_keys = sorted({key for play in plays for key in play})
    report = f"""# ESPN College Football Play-by-Play Schema Report

## Sample

- Event ID: `{event_id}`
- Summary endpoint: <{url}>
- Drives found: {len(drives)}
- Nested plays found: {len(plays)}
- Top-level scoring plays found: {scoring_plays}
- Unique play JSON paths found: {len(schema)}

## Location

For this completed college-football game, drive data is stored under
`drives.previous[]`, and each drive stores its play-by-play records under
`plays[]`. Therefore, the full path is `drives.previous[].plays[]`.

No separate play-by-play request is required for this extraction because the
game-summary response already contains the plays. The summary has a separate
top-level `scoringPlays[]` collection for scoring events.

## Direct drive fields

`{", ".join(direct_drive_keys)}`

## Direct play fields

`{", ".join(direct_play_keys)}`

## Notes

- The human-readable play description is stored in `text`, not `playText`.
- Some fields are optional. For example, scoring-related fields occur only on
  scoring plays, and point-after-attempt fields occur only when applicable.
- `play_by_play_schema.csv` lists every recursively discovered play path, its
  observed JSON type, an example value, and how many sample plays contain it.
- `sample_plays.csv` demonstrates a future relational, one-row-per-play table.
- ESPN's API is unofficial, so fields and endpoint behavior may change.
"""
    path.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map one ESPN college-football game's play-by-play schema."
    )
    parser.add_argument(
        "event_id",
        nargs="?",
        default="401856723",
        help="ESPN event ID (default: 401856723)",
    )
    parser.add_argument(
        "--output-dir",
        default="play_by_play_output",
        help="Directory for generated CSV and Markdown files",
    )
    args = parser.parse_args()

    payload, url = fetch_game(args.event_id)
    drives = collect_drives(payload)
    plays = [
        play
        for drive in drives
        for play in drive.get("plays", [])
        if isinstance(play, dict)
    ]

    if not drives:
        raise SystemExit("No drives were found in this game-summary response.")
    if not plays:
        raise SystemExit("Drives were found, but they contained no plays.")

    schema = build_schema(plays)
    flattened_plays = flatten_plays(args.event_id, drives)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(output_dir / "play_by_play_schema.csv", schema)
    write_csv(output_dir / "sample_plays.csv", flattened_plays)
    write_report(
        output_dir / "play_by_play_report.md",
        args.event_id,
        url,
        drives,
        plays,
        schema,
        len(payload.get("scoringPlays", [])),
    )

    print(f"Event ID: {args.event_id}")
    print(f"Drives found: {len(drives)}")
    print(f"Nested plays found: {len(plays)}")
    print(f"Unique play JSON paths found: {len(schema)}")
    print(f"Output directory: {output_dir.resolve()}")


if __name__ == "__main__":
    main()

