from datetime import datetime, timezone
from math import isfinite
import os
import numpy as np
import pandas as pd
from google.cloud import bigquery
from scipy.stats import poisson

from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
# ============================================================
# Configuration
# ============================================================

SOURCE_DATASET = "dbt_jose_intermediate"
SOURCE_TABLE = "int_match_features"

TARGET_DATASET = "predictions"
TARGET_TABLE = "poisson_predictions"

MAX_GOALS = 10


# ============================================================
# BigQuery
# ============================================================

client = bigquery.Client()


# ============================================================
# Get match features
# ============================================================

def get_match_features() -> pd.DataFrame:

    query = f"""
        SELECT
            fixture_id,
            season_id,
            team_id,
            opponent_team_id,
            is_home,
            avg_home_goals_scored,
            avg_home_goals_against,
            avg_away_goals_scored,
            avg_away_goals_against

        FROM `{PROJECT_ID}.{SOURCE_DATASET}.{SOURCE_TABLE}`
        ORDER BY fixture_id, is_home DESC
    """

    return client.query(query).to_dataframe()


# ============================================================
# Calculate Poisson lambdas
# ============================================================

def calculate_lambdas(match: pd.DataFrame) -> tuple[float, float]:

    home = match[match["is_home"] == True].iloc[0]
    away = match[match["is_home"] == False].iloc[0]

    lambda_home = (
        home["avg_home_goals_scored"]
        + away["avg_away_goals_against"]
    ) / 2

    lambda_away = (
        away["avg_away_goals_scored"]
        + home["avg_home_goals_against"]
    ) / 2

    return lambda_home, lambda_away


# ============================================================
# Calculate match probabilities
# ============================================================

def calculate_match_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = MAX_GOALS,
) -> tuple[float, float, float]:

    goals = np.arange(max_goals + 1)

    home_probabilities = poisson.pmf(goals, lambda_home)
    away_probabilities = poisson.pmf(goals, lambda_away)

    probability_matrix = np.outer(
        home_probabilities,
        away_probabilities
    )

    probability_home_win = np.tril(
        probability_matrix,
        k=-1
    ).sum()

    probability_draw = np.trace(probability_matrix)

    probability_away_win = np.triu(
        probability_matrix,
        k=1
    ).sum()

    return (
        probability_home_win,
        probability_draw,
        probability_away_win,
    )


# ============================================================
# Generate predictions
# ============================================================

def generate_predictions(
    match_features: pd.DataFrame,
) -> pd.DataFrame:

    predictions = []

    for fixture_id, match in match_features.groupby("fixture_id"):

        if len(match) != 2:
            print(
                f"Skipping fixture {fixture_id}: "
                f"expected 2 rows, found {len(match)}"
            )
            continue

        home = match[match["is_home"] == True]
        away = match[match["is_home"] == False]

        if home.empty or away.empty:
            print(
                f"Skipping fixture {fixture_id}: "
                "missing home or away team"
            )
            continue

        home = home.iloc[0]
        away = away.iloc[0]

        required_columns = [
            "avg_home_goals_scored",
            "avg_home_goals_against",
            "avg_away_goals_scored",
            "avg_away_goals_against",
        ]

        if any(
            pd.isna(home[column])
            for column in required_columns[:2]
        ) or any(
            pd.isna(away[column])
            for column in required_columns[2:]
        ):
            print(
                f"Skipping fixture {fixture_id}: "
                "missing team statistics"
            )
            continue

        lambda_home, lambda_away = calculate_lambdas(match)

        if (
            not isfinite(lambda_home)
            or not isfinite(lambda_away)
            or lambda_home < 0
            or lambda_away < 0
        ):
            print(
                f"Skipping fixture {fixture_id}: "
                "invalid lambda"
            )
            continue

        (
            probability_home_win,
            probability_draw,
            probability_away_win,
        ) = calculate_match_probabilities(
            lambda_home,
            lambda_away,
        )

        predictions.append({
            "fixture_id": fixture_id,
            "season_id": home["season_id"],
            "home_team_id": home["team_id"],
            "away_team_id": away["team_id"],
            "lambda_home": round(lambda_home, 3),
            "lambda_away": round(lambda_away, 3),
            "prob_home_win": round(probability_home_win, 3),
            "prob_draw": round(probability_draw, 3),
            "prob_away_win": round(probability_away_win, 3),
            "prediction_date": datetime.now(timezone.utc),
        })

    return pd.DataFrame(predictions)


# ============================================================
# Write predictions to BigQuery
# ============================================================

def write_predictions(predictions: pd.DataFrame) -> None:

    table_id = (
        f"{PROJECT_ID}.{TARGET_DATASET}.{TARGET_TABLE}"
    )

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_dataframe(
        predictions,
        table_id,
        job_config=job_config,
    )

    job.result()

    print(
        f"Successfully wrote "
        f"{len(predictions)} predictions to {table_id}"
    )


# ============================================================
# Main
# ============================================================

def main():

    print("Reading match features...")

    match_features = get_match_features()

    if match_features.empty:
        print("No matches found. Nothing to predict.")
        return

    print(
        f"Found {len(match_features)} team-match rows "
        f"for {match_features['fixture_id'].nunique()} fixtures."
    )

    print("Generating Poisson predictions...")

    predictions = generate_predictions(match_features)

    if predictions.empty:
        print("No predictions generated.")
        return

    print(
        f"Generated {len(predictions)} predictions."
    )

    write_predictions(predictions)


if __name__ == "__main__":
    main()