SELECT *
FROM {{ ref('fct_matches') }}
WHERE team_key = opponent_team_key