{{ config(
    materialized='incremental',
    unique_key='season_summary_key',
    incremental_strategy='merge',
) }}

WITH snapshot AS (
    SELECT CURRENT_DATE() AS snapshot_date
)

SELECT 
  {{ dbt_utils.generate_surrogate_key(['mcp.season_id', 't.team_key', 's.snapshot_date']) }} AS season_summary_key,
  t.team_key,
  mcp.season_id,
  cs.matches_played,
  cs.wins,
  cs.draws,
  cs.losses,
  mcp.title_probability AS title_probability,
  cs.goals_scored AS cumulative_goals_scored,
  cs.goals_against AS cumulative_goals_against,
  cs.goal_difference AS cumulative_goal_difference,
  cs.current_position AS league_position,
  cs.total_points AS cumulative_points,
  COALESCE(cs.total_points / NULLIF(cs.matches_played, 0), 0) AS points_per_game,
  s.snapshot_date
  FROM {{ source('predictions', 'montecarlo_predictions') }} mcp
  CROSS JOIN snapshot AS s
  JOIN {{ ref('int_current_standings') }} cs ON mcp.season_id = cs.season_id AND mcp.team_id = cs.team_id
  JOIN {{ ref('dim_team') }} t ON mcp.team_id = t.team_id AND 
  s.snapshot_date >= DATE(t.valid_from) 
  AND (s.snapshot_date < DATE(t.valid_to) OR DATE(t.valid_to) IS NULL)
