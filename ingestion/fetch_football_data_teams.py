import os
import requests
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = "raw"
TABLE_NAME = "raw_teams"
API_KEY = os.getenv("FOOTBALL_API_KEY")
API_URL = "https://api.football-data.org/v4/competitions/PD/teams"

def fetch_raw_teams():
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()
    
    return response.json().get("teams", [])

def load_to_bigquery(data):
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_NAME}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True
    )

    job = client.load_table_from_json(data, table_id, job_config=job_config)
    job.result()
    
    print(f"Loaded {len(data)} full team objects into {table_id}.")

if __name__ == "__main__":
    raw_teams = fetch_raw_teams()
    if raw_teams:
        load_to_bigquery(raw_teams)