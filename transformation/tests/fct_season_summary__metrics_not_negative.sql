SELECT *
FROM {{ ref('fct_season_summary') }}
WHERE matches_played < 0
   OR wins < 0
   OR draws < 0
   OR losses < 0
   OR cumulative_goals_scored < 0
   OR cumulative_goals_against < 0
   OR cumulative_points < 0
   OR points_per_game < 0