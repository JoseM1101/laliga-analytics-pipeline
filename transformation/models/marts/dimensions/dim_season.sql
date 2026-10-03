WITH season_data AS (

    SELECT
        season_id,
        MIN(season_start_date) AS season_start_date,
        MAX(season_end_date) AS season_end_date,
        MAX(season_winner) AS season_winner,
        COUNT(DISTINCT home_team_id) AS number_of_teams,
        MAX(matchday) AS number_of_matchdays,
        COUNT(*) AS number_of_matches
    FROM {{ ref('stg_api__matches') }}
    GROUP BY season_id
)

SELECT
    season_id,
    CONCAT(
        EXTRACT(YEAR FROM season_start_date),
        '/',
        EXTRACT(YEAR FROM season_end_date)
    ) AS season_name,
    season_start_date AS start_date,
    season_end_date AS end_date,
    number_of_teams,
    number_of_matchdays,
    number_of_matches,
    CURRENT_DATE() BETWEEN season_start_date AND season_end_date AS is_current,
    season_winner AS league_winner
FROM season_data