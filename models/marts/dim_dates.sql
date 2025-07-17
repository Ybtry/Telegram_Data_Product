    -- dbt_project/models/marts/dim_dates.sql
    -- Dimension table for dates.

    {{ config(materialized='table') }} -- Use 'table' for dimension tables

    WITH date_series AS (
        SELECT generate_series(
            '2019-01-01'::date, -- Start date to cover oldest data (adjust if needed)
            '2026-01-01'::date, -- End date to cover future data (adjust if needed)
            '1 day'::interval
        )::date AS date_day
    )
    SELECT
        date_day,
        EXTRACT(YEAR FROM date_day) AS year,
        EXTRACT(MONTH FROM date_day) AS month,
        EXTRACT(DAY FROM date_day) AS day,
        EXTRACT(DOW FROM date_day) AS day_of_week, -- 0=Sunday, 6=Saturday
        TO_CHAR(date_day, 'Day') AS day_name,
        EXTRACT(DOY FROM date_day) AS day_of_year,
        EXTRACT(WEEK FROM date_day) AS week_of_year,
        EXTRACT(QUARTER FROM date_day) AS quarter,
        TO_CHAR(date_day, 'YYYY-MM') AS year_month,
        TO_CHAR(date_day, 'YYYY-Q') AS year_quarter,
        CASE
            WHEN EXTRACT(DOW FROM date_day) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend
    FROM
        date_series
    ORDER BY
        date_day
    