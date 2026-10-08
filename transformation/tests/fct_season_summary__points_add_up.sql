SELECT *
FROM {{ ref('fct_season_summary') }}
WHERE cumulative_points != (wins * 3 + draws)