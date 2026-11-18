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
