# CFP Ranking Algorithm — Project Vision

> Read this before starting any work on ranking algorithms in this repo.
> It holds Connor's long-term goals so they don't need to be re-explained.
> Add new intentions to the **Intent Log** at the bottom as they come up.

## What this is
This work goes beyond the scope of the COSC445 ESPN data-mining project. The course
project (ESPN API schema discovery, the SQLite databases, box score and play-by-play
data) is the **data foundation**. The goal here is to build a
**College Football Playoff (CFP) ranking algorithm** on top of it.

## Core goal
Build a ranking system that **combines actual on-field performance with the
criteria the CFP Selection Committee says it uses**: in effect, an algorithmic
version of the committee's decision-making.

- **Not trying to replace the committee.** The aim is a tool the committee could use
  alongside its own judgment.
- **Disagreeing with the committee is expected.** The committee makes mistakes, and an
  algorithm that applies its own criteria consistently will sometimes land elsewhere.
  Known committee mistakes to correct for:
  - **Brand bias**: traditional powers placed higher than their results justify.
  - **Inconsistent justification**: placements that contradict the committee's own
    criteria. Example: Alabama ranked #3 and Tennessee #8 even though Tennessee
    beat Alabama 26–10 head-to-head.
- When our ranking differs from the committee's, we should be able to **explain why**
  using the criteria (e.g. "head-to-head result overrides the gap in resume").

## Committee criteria to model
The CFP selection protocol tells the committee to weigh the following, especially
when comparing teams that look similar:
- Championships won (conference titles)
- Strength of schedule
- Head-to-head results
- Comparative outcomes against common opponents
- Other relevant factors, such as key injuries that affected results or will affect
  availability

Together with **on-field performance metrics** taken from our ESPN data (efficiency,
margin, offensive and defensive stats, play-by-play measures), these are the inputs
the algorithm should combine.

## Immediate next step
Create a **new notebook for trying out different ranking algorithms**, using the data
already collected (`espn_cfb_2025.db`, `espn_cfb_2026.db`, the team and defensive CSVs).
Possible directions (none chosen yet):
- Rating models built only on performance (e.g. margin/efficiency-based power ratings,
  Elo, Massey/Colley-style systems)
- A resume score that scores the committee criteria explicitly
- Hybrid models that blend the two, with head-to-head and common-opponent
  constraints applied as adjustments
- Comparing each model against the committee's actual weekly rankings to find where
  and why they disagree

## Long-term goal
Create a **pipeline toward the committee actually using this**. That includes
contacting **conference commissioners/directors** and the **CFP executive
director**. The work should therefore be:
- **Transparent and explainable**: decision-makers must be able to follow why a team
  is ranked where it is.
- **Reproducible**: anyone can rerun it from the data and get the same rankings.
- **Defensible**: backtested against past seasons and committee rankings, with a
  clear story for where it improves on the committee (bias, consistency).

## Where we left off (update every session)
_Last updated 2026-11-23. Connor closed the session to work on other parts of the course project._

**Notebook state (`cfp_rankings.ipynb`):** Phases 1–3 are done and committed, up to
`df68ac4` ("deriving a reasonable cap margin for massey").
- Phase 1: `games` (Final games only, FCS IDs replaced with `"FCS"`), `teams` (plus the FCS
  row), `team_games` (one row per team per game: `team_id`, `opp_id`, `points_for`,
  `points_against`, `location`, `margin`, `win`).
- Phase 2: `records` (indexed by `team_id`: games, wins, losses, win_pct, sos (naive),
  colley, massey) and `ranking` (win % with SOS as a tiebreaker).
- Phase 3: Colley (`C r = b`, `colley_rank`); Massey (`X`, `y`, a sum-to-zero
  constraint row, `lstsq`, `massey_rank`, home-field advantage about 3.16 uncapped);
  helper functions `massey_ratings(X_c, y, cap=None)` (symmetric clip),
  `build_massey_system(games_df)`, `predict_margins(sol, test_games)` and
  `backtest(cap=None, start_week=5)`.
- Backtest (weeks 5–11, 421 games, scored on winner accuracy): no cap 65.3%, cap 35
  66.5%, **cap 28 67.0%**, cap 21 66.3%, cap 14 63.4%, cap 7 63.2%. Baseline "home team always
  wins" is 56.8%. The differences between 21, 28 and 35 are 2–3 games, which is
  noise. Conclusion so far: moderate caps beat both no cap and tight caps.
- Claude added the baseline cell (the last cell) at Connor's request. **It may not have been run
  or committed yet**, so check that first.

**NEXT TASK: garbage-time margin from play-by-play.** Connor wants to get this right.
Data is available: the `Plays` table covers all 752 Final 2026 games (and 956 of 958
in 2025). Each play has `period`, `clock` ("MM:SS"), and running `home_score` /
`away_score` after the play. `Scoring_Plays` also exists (`period`, `clock`,
`team_id`, `points`).
Plan (still pair-programming: guide Connor, don't write the cells):
1. Load the plays for Final games. Turn `period` + `clock` into elapsed seconds
   (quarters are 15:00; overtime is period ≥ 5, and a game in OT was never garbage time).
2. Define **"game decided"**. Start simple and transparent, e.g. the lead is ≥ N
   points with ≤ T seconds left (thresholds that vary by quarter, like SP+ style
   rules: Q2 > 38, Q3 > 28, Q4 > 22), or a lead greater than the points still
   possible in the time left. Keep N/T as parameters.
3. For each game, the **competitive margin** is the home-minus-away score at the
   first play where the game became decided (or the final margin if it never did). Watch out:
   a "decided" game where the trailing team came back. Decide whether to use the first
   decided moment or require the game to stay decided.
4. Check: there should be one competitive margin per game, and |competitive| should be ≤ |final|
   in almost every game. Look at examples (LSU's and Wake Forest's blowouts).
5. Plug it into Massey as an alternative `y`. This needs `massey_ratings` /
   `build_massey_system` / `backtest` to accept a margin column (e.g. a
   `margin_col` parameter) instead of always using `home_score - away_score`.
   Scoring should still be winner accuracy against the actual final result.
6. Put garbage-time Massey on the backtest scoreboard against caps 21/28/35. Only
   keep it if it beats the simple cap (the backtest is the judge).

**Backlog after garbage time (in recommended order):**
1. `load_season(db_path)` refactor so the whole pipeline also runs on 2025, then
   rerun the backtest scoreboard on 2025 to see whether the margin setting holds up.
2. `tanh` smooth cap (`k * tanh(m / k)`) as another scoreboard option.
3. Phase 4: resume score. First fix SOS self-inclusion (opponents' win % leaving out
   games against the team itself, which Connor identified), then score quality wins,
   bad losses (6 FBS teams lost to FCS in 2026) and conference titles.
4. Phase 5: blend Colley (resume) with Massey (strength), plus head-to-head and
   common-opponent adjustments. Test case: Tennessee beat Alabama 26–10 in Week 7
   (2026), but Colley has Alabama #6 / Tennessee #13 and Massey has #4 / #8 (about 6 points
   apart). Connor needs to decide when teams count as "comparable" enough for
   head-to-head to override the ratings.
5. Phase 6: compare everything with the committee's actual rankings.

## Intent Log
Add dated entries as new goals or decisions come up.

- **2026-11-18**: Vision set out: a CFP ranking algorithm that emulates the
  committee's criteria plus on-field performance; correct for brand bias and
  inconsistent justification; next step is an algorithm-experimentation notebook;
  end goal is adoption by the committee via outreach to conference directors and the
  CFP executive director.
- **2026-11-18**: **Working style: pair-programming.** For the ranking notebook,
  Claude guides and Connor writes all the code. Explain the goal and concept for
  each step, give hints, function names and small snippets, then review what Connor
  wrote. Don't write whole cells or large code blocks into the notebook unless asked.
  Notebook: `cfp_rankings.ipynb`.
- **2026-11-18**: **Modeling decision: FCS opponents.** All FCS teams (the
  `Teams` rows where `conference` is NULL, 102 of them in 2026) are combined into a
  single "FCS" pseudo-team. Their games are kept, so a loss to an FCS team still
  counts against an FBS team, and the rating stays stable. Only FBS teams appear in
  the final rankings.
- **2026-11-20**: **Modeling decision: margin handling in Massey.** No hand-picked
  margin cap. Connor prefers (a) **tuning by out-of-sample prediction**: fit on
  weeks 1..k-1, predict week k, roll forward, and choose the setting that predicts best,
  then check it on the 2025 season; and (b) **garbage-time filtering from
  play-by-play** (ignore points scored after the game is decided), which is the most
  principled approach. Plan: build the backtest first, so that hard caps, smooth
  caps (tanh) and garbage-time filtering can all be compared on the same measure.
  **Never tune parameters to match the committee's rankings**: that would build in
  its biases. Tune on predictive accuracy, then compare with the committee.
- **2026-11-26**: **Injury data.** ESPN has no college injury data, so injuries come from the
  conference availability reports, collected by kickoffstatus.com. `cfb2026.ipynb` section 10 stores
  them in `Raw_Injury_Pages` / `Injury_Reports` (2026 only; official reports cover conference games only,
  plus unofficial media notes). `matchup_simulator.ipynb` uses them (`INJURY_REPORTS`). Questionable is
  about 60% to play (Connor's estimate, confirmed by the data: 57% on the Wednesday report, 62% on gameday).
  The other chances are also measured from 2026 box scores. They are relevant to the committee's "key
  injuries" criterion later.
- **2026-11-26**: **Next simulator goal: recent playing style.** The matchup simulator underweights
  how a team has played in its last 2-3 games. Example: Tennessee's Faizon Brandon QB-run packages
  (Single Wing Shotgun) since Week 11. The simulator uses one QB per game, and the team pass-rate offset
  isn't recency-weighted.
- **Finding (2026-11-26):** The simulator gave every QB carry to the starter, so package-QB runs were
  simulated as the starter's. The fix is `PACKAGE_QBS`. Backtest, Weeks 7–12, 366 games: neutral
  overall (+0.0016 ± 0.0049 Brier). The 190 games with a package-QB team looked better at 40 sims
  (−0.0074), but a rerun at 150 sims showed that was noise (−0.0006 ± 0.0035). It's on because it's
  correct at the player level and costs no accuracy. Recency-weighting the run/pass tendency (`TENDENCY_DECAY` 0.7) and faster usage decay (0.6)
  didn't help overall, and 0.6 was worse, so both are off. No version improved the simulated run-share
  error (8.4 pts), so most of a team's game-to-game run/pass swing is game script.
- **Finding (2026-11-20):** Margin caps don't fix LSU-type profiles (blowout
  wins, close losses). Massey treats a 1-point loss as almost a tie. So the
  final model needs a win/loss (resume) component as well as margin.
