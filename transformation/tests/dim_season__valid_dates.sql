SELECT *
FROM {{ ref('dim_season') }}
WHERE start_date >= end_date