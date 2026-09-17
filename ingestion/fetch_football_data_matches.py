import os
import requests
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = "raw"
TABLE_NAME = "raw_matches"
API_KEY = os.getenv("FOOTBALL_API_KEY")
API_URL = "https://api.football-data.org/v4/competitions/PD/matches"

def fetch_raw_matches():
    headers = {"X-Auth-Token": API_KEY}
    
    print(f"Fetching matches...")
    response = requests.get(API_URL, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    matches = data.get("matches", [])

          
    return matches

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
    
    print(f"Loaded {len(data)} full match objects into {table_id}.")

if __name__ == "__main__":
    raw_matches = fetch_raw_matches()
    if raw_matches:
        load_to_bigquery(raw_matches)