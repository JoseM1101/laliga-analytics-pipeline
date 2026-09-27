WITH home_matches AS (
  SELECT
    {{dbt_utils.generate_surrogate_key(['home_team_id', 'match_id'])}} AS match_team_key,
    home_team_id AS team_id,
    away_team_id AS opponent_team_id,
    season_id,
    match_id AS fixture_id,
    TRUE AS is_home,
    match_date,
    home_team_score AS goals_scored,
    away_team_score AS goals_against,
    matchday,
    status,
    CASE 
      WHEN status = 'FINISHED' AND home_team_score > away_team_score THEN 3
      WHEN status = 'FINISHED' AND home_team_score = away_team_score THEN 1
      WHEN status = 'FINISHED' AND home_team_score < away_team_score THEN 0
      ELSE NULL 
    END AS points
  FROM {{ ref('stg_api__matches') }}
),
away_matches AS (
  SELECT
    {{dbt_utils.generate_surrogate_key(['away_team_id', 'match_id'])}} AS match_team_key,
    away_team_id AS team_id,
    home_team_id AS opponent_team_id,
    season_id,
    match_id AS fixture_id,
    FALSE AS is_home,
    match_date,
    away_team_score AS goals_scored,
    home_team_score AS goals_against,
    matchday,
    status,
    CASE 
      WHEN status = 'FINISHED' AND away_team_score > home_team_score THEN 3
      WHEN status = 'FINISHED' AND away_team_score = home_team_score THEN 1
      WHEN status = 'FINISHED' AND away_team_score < home_team_score THEN 0
      ELSE NULL 
    END AS points
  FROM {{ ref('stg_api__matches') }}
)

SELECT * FROM home_matches
UNION ALL
SELECT * FROM away_matches