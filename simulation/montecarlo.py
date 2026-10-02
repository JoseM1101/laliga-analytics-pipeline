import numpy as np
import pandas as pd
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ID = os.getenv("GCP_PROJECT_ID")

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

client = bigquery.Client()


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

standings = client.query(standings_query).to_dataframe()


# ---------------------------------------------------------
# Load remaining fixtures
# ---------------------------------------------------------

poisson_query = f"""
SELECT
    fixture_id,
    season_id,
    home_team_id,
    away_team_id,
    lambda_home,
    lambda_away
FROM `{POISSON_TABLE}`
"""

fixtures = client.query(poisson_query).to_dataframe()


# ---------------------------------------------------------
# Validate input
# ---------------------------------------------------------

if standings.empty:
    raise ValueError("Current standings table is empty.")

if fixtures.empty:
    raise ValueError("Poisson predictions table is empty.")


season_ids = standings["season_id"].unique()

if len(season_ids) != 1:
    raise ValueError(
        f"Expected one season in standings, found {len(season_ids)}."
    )

season_id = season_ids[0]

fixtures = fixtures[
    fixtures["season_id"] == season_id
].copy()


# ---------------------------------------------------------
# Prepare current standings
# ---------------------------------------------------------

teams = standings[
    [
        "team_id",
        "total_points",
        "goal_difference",
        "goals_scored",
    ]
].copy()

teams = teams.set_index("team_id")


# ---------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------

rng = np.random.default_rng()

championship_counts = {
    team_id: 0
    for team_id in teams.index
}


for _ in range(N_SIMULATIONS):

    # Start from the actual current standings.
    simulated_points = teams["total_points"].copy()
    simulated_goal_difference = teams["goal_difference"].copy()
    simulated_goals_scored = teams["goals_scored"].copy()

    # Simulate every remaining fixture.
    for _, fixture in fixtures.iterrows():

        home_team = fixture["home_team_id"]
        away_team = fixture["away_team_id"]

        lambda_home = fixture["lambda_home"]
        lambda_away = fixture["lambda_away"]

        # Generate goals using the Poisson distribution.
        home_goals = rng.poisson(lambda_home)
        away_goals = rng.poisson(lambda_away)

        # Update goals scored.
        simulated_goals_scored[home_team] += home_goals
        simulated_goals_scored[away_team] += away_goals

        # Update goal difference.
        goal_difference = home_goals - away_goals

        simulated_goal_difference[home_team] += goal_difference
        simulated_goal_difference[away_team] -= goal_difference

        # Update points.
        if home_goals > away_goals:

            simulated_points[home_team] += 3

        elif home_goals < away_goals:

            simulated_points[away_team] += 3

        else:

            simulated_points[home_team] += 1
            simulated_points[away_team] += 1

    # -----------------------------------------------------
    # Determine champion
    # -----------------------------------------------------

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

results = pd.DataFrame([
    {
        "season_id": season_id,
        "team_id": team_id,
        "simulation_count": N_SIMULATIONS,
        "championship_count": count,
        "title_probability": count / N_SIMULATIONS,
    }
    for team_id, count in championship_counts.items()
])


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

print(f"Monte Carlo predictions written to {OUTPUT_TABLE}")