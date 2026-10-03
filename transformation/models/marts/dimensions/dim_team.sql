SELECT
    dbt_scd_id AS team_key,
    team_id,
    name,
    coach,
    stadium,
    foundation_year,
    badge_url,
    dbt_valid_from AS valid_from,
    dbt_valid_to AS valid_to
FROM {{ ref('team_snapshot') }}