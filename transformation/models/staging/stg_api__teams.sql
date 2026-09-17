SELECT 
  id AS team_id,
  name,
  coach.name AS coach,
  venue AS stadium,
  founded AS foundation_year,
  crest AS badge_url
FROM {{ source('football_data', 'raw_teams') }}


  