-- dbt_project/models/staging/stg_telegram_messages.sql
-- This model cleans and extracts key fields from the raw JSON messages.

{{ config(materialized='view') }} -- Use 'view' for staging models for flexibility

SELECT
    (message_data->>'id')::BIGINT AS message_id,
    (message_data->>'date')::TIMESTAMP WITH TIME ZONE AS message_timestamp,
    message_data->>'message' AS message_text,
    (message_data->>'sender_id')::BIGINT AS sender_id,
    -- Use peer_id as channel_id, as it's typically the correct channel identifier
    (message_data->>'peer_id')::BIGINT AS channel_id,
    (message_data->>'views')::INT AS views_count,
    (message_data->>'forwards')::INT AS forwards_count,
    (message_data->>'replies')::INT AS replies_count,
    message_data->>'post_author' AS post_author,
    (message_data->>'grouped_id')::BIGINT AS grouped_id,
    message_data->>'url' AS message_url,
    -- Corrected: Derive has_image based on 'has_media' and 'media_type'
    (message_data->>'has_media')::BOOLEAN AND (message_data->>'media_type' = 'MessageMediaPhoto') AS has_image,
    -- Extract and clean image file path if available and it's a photo
   
    CASE
        WHEN (message_data->>'has_media')::BOOLEAN AND (message_data->>'media_type' = 'MessageMediaPhoto') THEN
            REPLACE(
                SUBSTRING(
                    message_data->>'file',
                    LENGTH('data\\raw\\telegram_media\\') + 1
                ),
                '\',
                '/'
            )
        ELSE NULL
    END AS image_file_path,
    source_file,
    loaded_at
FROM
    {{ source('raw', 'telegram_messages') }}
WHERE
    message_data IS NOT NULL -- Ensure message_data exists
