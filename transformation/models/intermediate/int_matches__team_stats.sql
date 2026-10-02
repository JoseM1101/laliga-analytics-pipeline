{{ config(
    materialized='table',
    cluster_by=['season_id', 'team_id']
) }}

SELECT
  team_id,
  season_id,
  ROUND(AVG(
    CASE WHEN is_home THEN goals_scored END
  ), 2) AS avg_home_goals_scored,
  ROUND(AVG(
    CASE WHEN is_home THEN goals_against END
  ), 2) AS avg_home_goals_against,
  ROUND(AVG(
    CASE WHEN NOT is_home THEN goals_scored END
  ), 2) AS avg_away_goals_scored,
  ROUND(AVG(
    CASE WHEN NOT is_home THEN goals_against END
  ), 2) AS avg_away_goals_against,
FROM {{ ref('int_matches__pivoted_by_team') }}
WHERE status = 'FINISHED'
GROUP BY team_id, season_id