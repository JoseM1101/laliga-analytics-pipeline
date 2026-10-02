WITH standings AS (
    SELECT
        team_id,
        season_id,
        COUNT(*) AS matches_played,
        COUNTIF(points = 3) AS wins,
        COUNTIF(points = 1) AS draws,
        COUNTIF(points = 0) AS losses,
        SUM(goals_scored) AS goals_scored,
        SUM(goals_against) AS goals_against,
        SUM(goals_scored) - SUM(goals_against) AS goal_difference,
        SUM(points) AS total_points
    FROM {{ ref('int_matches__pivoted_by_team') }}
    WHERE status = 'FINISHED'
    GROUP BY
        team_id,
        season_id
)

SELECT
    *,
    ROW_NUMBER() OVER (
        PARTITION BY season_id
        ORDER BY total_points DESC,
        goal_difference DESC,
        goals_scored DESC
    ) AS current_position

FROM standings