{% snapshot team_snapshot %}

{{
  config(
    target_schema='snapshots',
    unique_key='team_id',
    strategy='check',
    check_cols=['name', 'coach', 'stadium', 'badge_url']
  )
}}

SELECT 
  team_id,
  name,
  coach,
  stadium,
  foundation_year,
  badge_url
FROM {{ ref('stg_api__teams') }}

{% endsnapshot %}