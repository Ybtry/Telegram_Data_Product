        
        SELECT
            message_id
        FROM
            {{ ref('fct_messages') }}
        WHERE
            contains_price_keyword = TRUE
            AND message_text IS NULL
        