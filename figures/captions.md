# Presentation figures

Source: espn_cfb_2026.db (ESPN site API) · 822 Final games through Week 12 (Nov 21, 2026) · generated 2026-11-24. Regenerate by running cfb2026_stats.ipynb from the top.

- **01_api_gap** (`01_api_gap.png`, `01_api_gap.svg`): ESPN publishes team stats only for the offense and player stats for both sides, so team defense (yards, points and 3rd downs allowed) has to be reconstructed.
- **02_api_payload_tree** (`02_api_payload_tree.png`, `02_api_payload_tree.svg`): Standings, scoreboard and game summary endpoints cover teams, schedule and every play; the summary's box score has team stats for the offense only.
- **03_collection_pipeline** (`03_collection_pipeline.png`, `03_collection_pipeline.svg`): Only three steps call ESPN (952 requests for the season so far); parsing and deriving rebuild every table from stored JSON with zero requests.
- **04_collection_tiles** (`04_collection_tiles.png`, `04_collection_tiles.svg`): 822 completed games yield 419,826 player stat rows and 146,310 plays, all stored in one espn_cfb_2026.db file.
- **05_reconstruction_flow** (`05_reconstruction_flow.png`, `05_reconstruction_flow.svg`): Opponent box scores, the scoreboard, scoring plays and player box scores combine into 27 team defensive stats for each of 1,644 team-games.
- **06_before_after** (`06_before_after.png`, `06_before_after.svg`): ESPN publishes no team defensive stats; we reconstructed 17 plus 10 player totals per team-game and 63 season features per team.
- **07_worked_example** (`07_worked_example.png`, `07_worked_example.svg`): In Alabama at Tennessee, Alabama's offensive box score becomes Tennessee's "allowed" line, and 9 Tennessee defenders sum to 5 sacks, 10 TFL and 4 passes defended.
- **08_validation_agreement** (`08_validation_agreement.png`, `08_validation_agreement.svg`): Out of 1,644 team-games, the two sources agree exactly on interceptions in 1,644, fumble recoveries in 1,635, sacks in 1,549 and points in 1,641.
- **09_validation_checklist** (`09_validation_checklist.png`, `09_validation_checklist.svg`): 6 of 7 validation checks pass exactly or are fully explained; the exception (player sacks = sacks taken (play-by-play)) shows small disagreements between ESPN's own sources.
- **10_context_recovery** (`10_context_recovery.png`, `10_context_recovery.svg`): 9 of 9 fumble mismatches are explained by the play text (7 touchbacks, 1 own-fumble recovery, 1 muffed punt), and three play-text fixes raise exact sack agreement from 85.8% to 94.2%.
- **11_coverage** (`11_coverage.png`, `11_coverage.svg`): 16 of 17 opponent-derived stats and 7 of 10 player totals cover every team-game; offensePointsAllowed falls back to pointsAllowed in 3, interception rows exist only when a team has one, and QB hits and forced fumbles are not in ESPN's data.
- **12_case_study_tennessee** (`12_case_study_tennessee.png`, `12_case_study_tennessee.svg`): Tennessee's reconstructed defense allowed 282.9 total yards and 13.5 offensive points per game, and the per-game values average exactly to the season rollup.
- **13_fbs_distribution** (`13_fbs_distribution.png`, `13_fbs_distribution.svg`): Among 138 FBS defenses, Tennessee ranks 11th in total yards allowed, 5th in offensive points allowed, 4th in takeaways and 1st in sacks (1st = best).
- **14_ranking_movers** (`14_ranking_movers.png`, `14_ranking_movers.svg`): With CFP weights and opponent adjustment, Notre Dame moves from 8 to 1 while raw leader New Mexico falls to 11.
