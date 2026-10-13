SELECT
    {{ dbt_utils.generate_surrogate_key(['team_id']) }} AS team_key,
    team_id,
    name,
    coach,
    stadium,
    foundation_year,
    badge_url
FROM {{ ref('stg_api__teams') }}