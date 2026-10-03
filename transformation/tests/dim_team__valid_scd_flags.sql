SELECT *
FROM {{ ref('dim_team') }}
WHERE valid_to IS NOT NULL
  AND valid_to <= valid_from