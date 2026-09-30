SELECT
    m.fixture_id,
    m.season_id,
    m.team_id,
    m.opponent_team_id,
    m.is_home,
    s.avg_home_goals_scored,
    s.avg_home_goals_against,
    s.avg_away_goals_scored,
    s.avg_away_goals_against
FROM {{ ref('int_matches__pivoted_by_team') }} m
LEFT JOIN {{ ref('int_matches__team_stats') }} s
    ON m.team_id = s.team_id
    AND m.season_id = s.season_id
WHERE m.status != 'FINISHED'