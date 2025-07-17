-- dbt_project/models/marts/dim_channels.sql
-- Dimension table for Telegram channels.

{{ config(materialized='table') }} -- Use 'table' for dimension tables

WITH unique_channels AS (
    SELECT
        channel_id,
        
        COALESCE(SPLIT_PART(source_file, '.json', 1), 'Unknown Channel') AS channel_name,
        MIN(message_timestamp) AS first_seen_at,
        MAX(message_timestamp) AS last_seen_at
    FROM
        {{ ref('stg_telegram_messages') }}
    WHERE channel_id IS NOT NULL -- Only include valid channel IDs
    GROUP BY
        channel_id,
        channel_name
)
SELECT
    -- Replaced dbt_utils.generate_surrogate_key with a standard SQL MD5 hash
    MD5(CAST(channel_id AS TEXT) || channel_name) AS channel_sk, -- Surrogate key for joins
    channel_id,
    channel_name,
    first_seen_at,
    last_seen_at
FROM
    unique_channels
