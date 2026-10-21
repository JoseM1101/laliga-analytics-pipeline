
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID is not set in the environment.")

STANDINGS_TABLE = (
    f"{PROJECT_ID}.dbt_jose_intermediate.int_current_standings"
)

POISSON_TABLE = (
    f"{PROJECT_ID}.predictions.poisson_predictions"
)

OUTPUT_TABLE = (
    f"{PROJECT_ID}.predictions.montecarlo_predictions"
)

N_SIMULATIONS = 10_000


# ---------------------------------------------------------
# BigQuery client
# ---------------------------------------------------------

client = bigquery.Client(project=PROJECT_ID)


# ---------------------------------------------------------
# Load current standings
# ---------------------------------------------------------

standings_query = f"""
SELECT
    team_id,
    season_id,
    matches_played,
    wins,
    draws,
    losses,
    goals_scored,
    goals_against,
    goal_difference,
    total_points,
    current_position
FROM `{STANDINGS_TABLE}`
"""

standings = client.query(standings_query).to_dataframe(
    create_bqstorage_client=False
)


# ---------------------------------------------------------
# Load remaining fixtures and pivot Poisson predictions
# ---------------------------------------------------------

poisson_query = f"""
SELECT
    fixture_id,
    season_id,

    MAX(IF(is_home, team_id, NULL)) AS home_team_id,
    MAX(IF(NOT is_home, team_id, NULL)) AS away_team_id,

    MAX(IF(is_home, `lambda`, NULL)) AS lambda_home,
    MAX(IF(NOT is_home, `lambda`, NULL)) AS lambda_away

FROM `{POISSON_TABLE}`
GROUP BY
    fixture_id,
    season_id
"""

fixtures = client.query(poisson_query).to_dataframe(
    create_bqstorage_client=False
)


# ---------------------------------------------------------
# Validate input
# ---------------------------------------------------------

if standings.empty:
    raise ValueError("Current standings table is empty.")

if fixtures.empty:
    raise ValueError("Poisson predictions table is empty.")

if standings["team_id"].duplicated().any():
    raise ValueError("Standings contain duplicate team_id values.")

if standings["season_id"].isna().any():
    raise ValueError("Standings contain NULL season_id values.")

season_ids = standings["season_id"].unique()

if len(season_ids) != 1:
    raise ValueError(
        f"Expected one season in standings, found {len(season_ids)}."
    )

season_id = season_ids[0]

fixtures = fixtures[
    fixtures["season_id"] == season_id
].copy()

if fixtures.empty:
    raise ValueError(
        f"No Poisson fixtures found for season_id {season_id}."
    )

required_fixture_columns = [
    "home_team_id",
    "away_team_id",
    "lambda_home",
    "lambda_away",
]

if fixtures[required_fixture_columns].isna().any().any():
    raise ValueError(
        "Some fixtures have missing team IDs or lambdas. "
        "Check that each fixture has one home row and one away row."
    )

if (fixtures[["lambda_home", "lambda_away"]] < 0).any().any():
    raise ValueError("Poisson lambdas cannot be negative.")

if fixtures["fixture_id"].duplicated().any():
    raise ValueError(
        "More than one row exists per fixture after pivoting."
    )

teams = standings[
    [
        "team_id",
        "total_points",
        "goal_difference",
        "goals_scored",
    ]
].copy()

teams = teams.set_index("team_id")

team_ids = set(teams.index)

fixture_team_ids = (
    set(fixtures["home_team_id"])
    | set(fixtures["away_team_id"])
)

unknown_teams = fixture_team_ids - team_ids

if unknown_teams:
    raise ValueError(
        f"Fixtures contain teams missing from standings: {unknown_teams}"
    )


# ---------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------

rng = np.random.default_rng()

championship_counts = {
    team_id: 0
    for team_id in teams.index
}

print(
    f"Running {N_SIMULATIONS:,} simulations "
    f"for season_id {season_id} "
    f"across {len(fixtures)} remaining fixtures..."
)

for simulation in range(N_SIMULATIONS):

    # Start from the actual current standings.
    simulated_points = teams["total_points"].copy()
    simulated_goal_difference = teams["goal_difference"].copy()
    simulated_goals_scored = teams["goals_scored"].copy()

    # Simulate every remaining fixture.
    for fixture in fixtures.itertuples(index=False):

        home_team = fixture.home_team_id
        away_team = fixture.away_team_id

        lambda_home = fixture.lambda_home
        lambda_away = fixture.lambda_away

        # Generate goals from each team's Poisson distribution.
        home_goals = rng.poisson(lambda_home)
        away_goals = rng.poisson(lambda_away)

        # Update goals scored.
        simulated_goals_scored[home_team] += home_goals
        simulated_goals_scored[away_team] += away_goals

        # Update goal difference.
        goal_difference = home_goals - away_goals

        simulated_goal_difference[home_team] += goal_difference
        simulated_goal_difference[away_team] -= goal_difference

        # Award league points.
        if home_goals > away_goals:
            simulated_points[home_team] += 3

        elif home_goals < away_goals:
            simulated_points[away_team] += 3

        else:
            simulated_points[home_team] += 1
            simulated_points[away_team] += 1

    # Determine the champion using the project's tiebreaker order.
    final_table = pd.DataFrame({
        "team_id": teams.index,
        "points": simulated_points.values,
        "goal_difference": simulated_goal_difference.values,
        "goals_scored": simulated_goals_scored.values,
    })

    final_table = final_table.sort_values(
        by=[
            "points",
            "goal_difference",
            "goals_scored",
            "team_id",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
    )

    champion = final_table.iloc[0]["team_id"]

    championship_counts[champion] += 1


# ---------------------------------------------------------
# Build output
# ---------------------------------------------------------

prediction_timestamp = datetime.now(timezone.utc)

results = pd.DataFrame([
    {
        "season_id": season_id,
        "team_id": team_id,
        "simulation_count": N_SIMULATIONS,
        "championship_count": count,
        "title_probability": count / N_SIMULATIONS,
        "prediction_timestamp": prediction_timestamp,
    }
    for team_id, count in championship_counts.items()
])

# Confirm that the simulated title probabilities sum to 1.
total_probability = results["title_probability"].sum()

if not np.isclose(total_probability, 1.0):
    raise ValueError(
        f"Title probabilities sum to {total_probability}, not 1."
    )

results = results.sort_values(
    "title_probability",
    ascending=False
)

print("\nSimulated title probabilities:")
print(
    results[
        ["team_id", "championship_count", "title_probability"]
    ].to_string(index=False)
)


# ---------------------------------------------------------
# Write to BigQuery
# ---------------------------------------------------------

job_config = bigquery.LoadJobConfig(
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
)

job = client.load_table_from_dataframe(
    results,
    OUTPUT_TABLE,
    job_config=job_config,
)

job.result()

print(f"\nMonte Carlo predictions written to {OUTPUT_TABLE}")
