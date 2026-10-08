SELECT *
FROM {{ ref('fct_season_summary') }}
WHERE wins + draws + losses != matches_played