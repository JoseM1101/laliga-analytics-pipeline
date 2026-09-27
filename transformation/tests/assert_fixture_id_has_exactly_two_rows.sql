SELECT 
  fixture_id,
  COUNT(*) AS row_count
FROM {{ ref('int_matches__pivoted_by_team') }}
GROUP BY fixture_id
HAVING COUNT(*) != 2