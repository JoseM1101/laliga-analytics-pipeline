# LaLiga Analytics — Data Catalog

## Overview

This catalog summarizes the dbt models, their purpose, grain, and key logic. It reflects the **current implementation** in the supplied `transformation/` project. The star schema diagram may show intended design choices that are not fully implemented in the warehouse.

The dbt workflow transforms raw API data and Python-generated prediction outputs into analytical tables for match and season analysis.

## Sources

| Source | Purpose |
|---|---|
| `football_data.raw_matches` | Raw match, score, season, and fixture information from the football API |
| `football_data.raw_teams` | Raw team attributes such as name, coach, stadium, and badge |
| `predictions.poisson_predictions` | Python-generated match outcome probabilities |
| `predictions.montecarlo_predictions` | Python-generated season title probabilities |

Prediction formulas and simulation settings live outside the supplied dbt project and should be documented alongside the Python scripts.

## Staging models

| Model | Grain | Purpose |
|---|---|---|
| `stg_api__matches` | One row per match | Selects and renames fields from the nested raw match payload; casts full-time scores to integers. |
| `stg_api__teams` | One row per team | Selects and renames team attributes from the raw team payload. |

## Intermediate models

| Model | Grain | Purpose and key logic |
|---|---|---|
| `int_matches__pivoted_by_team` | One row per team per fixture | Converts each match into two team-relative rows. Calculates goals scored/conceded and points for finished matches (3 for a win, 1 for a draw, 0 for a loss). |
| `int_matches__team_stats` | One row per team per season | Calculates average home/away goals scored and conceded from finished matches. Materialized as a table clustered by `season_id` and `team_id`. |
| `int_match_features` | One row per non-finished team-fixture record, where team statistics match | Combines non-finished fixture details with the focal team's historical home/away goal averages for prediction inputs. |
| `int_current_standings` | One row per team per season | Aggregates finished matches into played, wins, draws, losses, goals, goal difference, points, and calculated league position. Position is ordered by points, goal difference, then goals scored. |

## Mart dimensions

### `dim_team`

- **Grain:** One row per team in the current implementation.
- **Purpose:** Provides descriptive team attributes for analytical models.
- **Key fields:** `team_key`, `team_id`, `name`, `coach`, `stadium`, `foundation_year`, `badge_url`.
- **Key logic:** `team_key` is generated from `team_id`.

**Design note:** The star schema diagram represents the intended SCD Type 2 design, but the current BigQuery implementation does not maintain historical team versions or effective-date columns. The catalog describes the implementation, not the intended diagram behavior.

### `dim_season`

- **Grain:** One row per season.
- **Purpose:** Provides season-level context.
- **Key fields:** `season_id`, `season_name`, `start_date`, `end_date`, `number_of_teams`, `number_of_matchdays`, `number_of_matches`, `is_current`, `league_winner`.
- **Key logic:** `season_name` is derived from the season start/end years; `is_current` is based on the current date.

## Mart facts

### `fct_matches`

- **Grain:** One row per team per fixture; each fixture is expected to produce two rows.
- **Purpose:** Supports team-relative match analysis and reporting.
- **Upstream:** `int_matches__pivoted_by_team`, `dim_team`, and `predictions.poisson_predictions`.
- **Key fields:** `match_team_key`, `team_key`, `opponent_team_key`, `season_id`, `fixture_id`, `is_home`, `match_date`, `goals_scored`, `goals_against`, `matchday`, `status`, `win_probability`, `draw_probability`, `loss_probability`, `points`.
- **Key logic:** Joins team-relative match records to team keys and prediction probabilities. The prediction join is a left join, so a match can remain in the fact even if its prediction fields are missing.

### `fct_season_summary`

- **Grain:** One row per team, season, and snapshot date.
- **Purpose:** Records current standings and simulated title probability over time.
- **Upstream:** `int_current_standings`, `dim_team`, and `predictions.montecarlo_predictions`.
- **Key fields:** `season_summary_key`, `team_key`, `season_id`, `matches_played`, `wins`, `draws`, `losses`, `title_probability`, `cumulative_goals_scored`, `cumulative_goals_against`, `cumulative_goal_difference`, `league_position`, `cumulative_points`, `points_per_game`, `snapshot_date`.
- **Materialization:** Incremental BigQuery model, partitioned by `snapshot_date` using `insert_overwrite`.
- **Key logic:** Joins simulated title probabilities to current standings. `snapshot_date` uses `CURRENT_DATE()`, so repeated runs on the same day target the same date partition.

## Business definitions

| Metric | Definition |
|---|---|
| Match points | 3 for a win, 1 for a draw, 0 for a loss; null for unfinished matches |
| Goal difference | Goals scored minus goals conceded |
| League position | `ROW_NUMBER()` ordered by points, goal difference, then goals scored |
| Points per game | Cumulative points divided by matches played, rounded to two decimals; zero when matches played is zero |
| Match outcome probabilities | Sourced from the Python-generated Poisson prediction table |
| Title probability | Sourced from the Python-generated Monte Carlo prediction table |

## Data quality and limitations

The project includes dbt tests for key uniqueness and non-null constraints, relationships between fact keys and dimensions, valid points, two team-relative rows per fixture, and consistency of season summary totals.

Keep these limitations in mind:

- **SCD Type 2:** Shown in the star schema as intended design, but not implemented in the current `dim_team` SQL due to project implementation constraints.
- **Standings:** The calculated position uses points, goal difference, and goals scored; it does not implement every official league tie-break rule.
- **Predictions:** The dbt project consumes prediction outputs but does not contain the Python calculation logic.
- **Snapshots:** Repeated runs on the same date target the same `snapshot_date` partition.
- **Pipeline scope:** This catalog covers the supplied dbt project. Ingestion behavior, Python implementation details, and dashboard usage should be documented from those components separately.
