SELECT *
FROM {{ ref('dim_seasons') }}
WHERE start_date >= end_date