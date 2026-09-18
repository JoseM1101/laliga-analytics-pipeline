SELECT
  id AS match_id,
  season.id AS season_id,
  season.startDate AS season_start_date,
  season.endDate AS season_end_date,
  homeTeam.id AS home_team_id,
  awayTeam.id AS away_team_id,
  homeTeam.name AS home_team_name,
  awayTeam.name AS away_team_name,
  utcDate AS match_date,
  SAFE_CAST(score.fullTime.home AS INT64) AS home_team_score,
  SAFE_CAST(score.fullTime.away AS INT64) AS away_team_score,
  status
FROM {{ source('football_data', 'raw_matches') }}

