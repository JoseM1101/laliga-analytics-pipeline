{{ config(
    materialized='table',
    cluster_by=['season_id', 'team_key']
) }}

SELECT 
  m.match_team_key,
  ht.team_key AS team_key,
  awt.team_key AS opponent_team_key,
  m.season_id,
  m.fixture_id,
  m.is_home,
  m.match_date,
  m.goals_scored,
  m.goals_against,
  m.matchday,
  m.status,
  p.win_probability,
  p.draw_probability,
  p.loss_probability,
  points
FROM {{ ref('int_matches__pivoted_by_team') }} m
JOIN {{ ref('dim_team') }} ht
    ON m.team_id = ht.team_id
JOIN {{ ref('dim_team') }} awt
    ON m.opponent_team_id = awt.team_id
LEFT JOIN {{ source('predictions', 'poisson_predictions') }} p ON m.fixture_id = p.fixture_id AND m.team_id = p.team_id