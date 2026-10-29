# LaLiga Analytics Pipeline

An end-to-end football analytics project that transforms LaLiga data into analytical datasets and probabilistic predictions. Built with Python, Google BigQuery, and dbt, the pipeline combines data ingestion, dimensional modeling, match outcome prediction, and Monte Carlo simulation to estimate teams' chances of winning the league.

## Project Overview

The goal of this project is to transform football data into structured, analysis-ready datasets for reporting and analysis.

Key components:
- **Data ingestion:** Retrieve match and team data from a football data API and load it into BigQuery.
- **Data transformation:** Clean, reshape, and prepare data through modular dbt staging, intermediate, and mart models.
- **Match predictions:** Use a Poisson-based model informed by current-season data and team performance to estimate match outcome probabilities.
- **League simulation:** Use Monte Carlo simulation to estimate each team's probability of winning the league based on current standings and match predictions.
- **Dimensional modeling:** Build fact and dimension tables for match analysis and season-level reporting.
- **Visualization:** Expose analytical datasets through a Data Studio dashboard.

## Architecture

The pipeline follows this general flow:

**Football Data API → BigQuery raw data → dbt staging and intermediate models → Python prediction scripts → BigQuery prediction tables → dbt marts → Data Studio**

Python prediction scripts use prepared warehouse data to generate predictions, write the results back to BigQuery, and make them available to downstream dbt models.

[LaLiga Data Lineage](docs/LaLiga_Analytics_Data_Lineage.png)

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data ingestion, Poisson predictions, and Monte Carlo simulation |
| SQL | Data transformations and analytical modeling |
| Google BigQuery | Cloud data warehouse |
| dbt | Modular SQL transformations and data modeling |
| Data Studio | Dashboarding and visualization |
| Git | Version control |

## Data Modeling

The analytical layer follows a dimensional modeling approach inspired by Kimball methodology.

| Model | Purpose |
|---|---|
| `dim_team` | Team attributes used for analysis |
| `dim_season` | Season-level attributes |
| `fct_matches` | Team-relative match records, including results and predicted outcome probabilities |
| `fct_season_summary` | Team-level season snapshots, including title probabilities and cumulative standings metrics |

The grain of `fct_matches` is one row per team per fixture. `fct_season_summary` records one row per team, and snapshot date.

See the [Data Catalog](docs/data_catalog.md) for model definitions, grains, dependencies, and implementation notes.

See the [LaLiga star schema](docs/LaLiga_Analytics_Star_Schema.png) for fact tables, dimensions, keys and relationships

## Prediction Models

### Poisson Match Predictions

The Poisson-based model estimates goal-scoring rates using current-season match data and team performance. These estimates are used to calculate possible scoreline probabilities and derive team-relative win, draw, and loss probabilities for each fixture.

### Monte Carlo League Simulation

Monte Carlo simulation uses current league standings and match outcome predictions to simulate possible season outcomes. The results estimate each team's probability of winning the league.

Both methods produce probabilistic estimates that depend on the available data and model assumptions; they do not guarantee future results.

## Dashboard

Explore the interactive Data Studio dashboard to see the analytical outputs produced by the pipeline.

**[View the Data Studio Dashboard](https://datastudio.google.com/reporting/d4f7a734-d991-4ee9-a5a5-f631f56c88ae/page/UccBG)**


## Repository Structure

```text
.
├── docs/
│   ├── data_catalog.md
│   ├── LaLiga Analytics Data Lineage.drawio
│   ├── LaLiga Analytics Star Schema.drawio
│   ├── LaLiga_Analytics_Data_Lineage.png
│   └── LaLiga_Analytics_Star_Schema.png
├── ingestion/
├── simulation/
├── transformation/
└── README.md
```

- `ingestion/` — source data extraction and loading.
- `simulation/` — Python prediction and simulation components.
- `transformation/` — dbt project containing staging, intermediate, and mart models.
- `docs/` — data catalog, lineage and star schema

## Setup and Execution

### Prerequisites

- Python and the required project dependencies.
- A Google Cloud project with BigQuery access.
- Google Cloud credentials with the permissions required by the pipeline.
- Access to the source football data API.
- dbt with the BigQuery adapter.

### Configuration

1. Clone the repository.
2. Install the dependencies required by the ingestion, simulation, and transformation components.
3. Configure the required environment variables and API credentials locally.
4. Configure dbt's BigQuery connection using your local dbt profile.
5. Verify that the required BigQuery datasets and permissions are available.

Keep API keys, service account credentials, and other secrets out of version control.

### Running the Pipeline

Run the components in their dependency order:

1. Ingest source data into BigQuery.
2. Run the required dbt staging and intermediate transformations.
3. Execute the Poisson prediction script.
4. Run the Monte Carlo simulation using the required prediction and standings data.
5. Run the downstream dbt models to build or update the analytical marts.
6. Refresh the Data Studio dashboard as needed.

The pipeline currently runs on demand and requires manual coordination of its execution steps.

## Limitations

- Match predictions depend on current-season data, team performance estimates, and the assumptions of the Poisson model.
- League-title probabilities depend on the current standings, match predictions, and Monte Carlo simulation assumptions.
- Results reflect the data available when the pipeline is executed.
- Pipeline execution is not yet fully automated through an orchestration schedule.
- The project is a portfolio implementation rather than a production system with comprehensive operational monitoring.