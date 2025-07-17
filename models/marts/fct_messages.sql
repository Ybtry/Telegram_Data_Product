    -- dbt_project/models/marts/fct_messages.sql
    -- Fact table for Telegram messages, linked to channel and date dimensions.

    {{ config(materialized='table') }} -- Use 'table' for fact tables

    SELECT
        stm.message_id,
        dc.channel_sk, -- Foreign key to dim_channels
        dd.date_day AS message_date, -- Foreign key to dim_dates
        stm.message_text,
        stm.sender_id,
        stm.views_count,
        stm.forwards_count,
        stm.replies_count,
        stm.post_author,
        stm.grouped_id,
        stm.message_url,
        stm.has_image,
        stm.image_file_path, -- Include image file path for YOLO in Task 3
        -- Add any other calculated metrics here
        LENGTH(stm.message_text) AS message_length,
        CASE
            WHEN stm.message_text ILIKE '%price%' OR stm.message_text ILIKE '%birr%' THEN TRUE
            ELSE FALSE
        END AS contains_price_keyword, -- Example of a simple business logic flag
        -- Add more flags for other business questions if needed
        CASE
            WHEN stm.message_text ILIKE '%drug%' OR stm.message_text ILIKE '%medication%' THEN TRUE
            ELSE FALSE
        END AS contains_drug_keyword,
        CASE
            WHEN stm.message_text ILIKE '%cream%' OR stm.message_text ILIKE '%cosmetic%' THEN TRUE
            ELSE FALSE
        END AS contains_cosmetic_keyword
    FROM
        {{ ref('stg_telegram_messages') }} stm
    LEFT JOIN
        {{ ref('dim_channels') }} dc ON stm.channel_id = dc.channel_id
    LEFT JOIN
        {{ ref('dim_dates') }} dd ON stm.message_timestamp::date = dd.date_day
    