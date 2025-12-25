{{
    config(
        materialized='view'
    )
}}

with source as (
    -- Deduplicate by taking the most recent record per step_id
    select *
    from (
        select *,
               row_number() over (partition by step_id order by created_at desc) as rn
        from {{ source('cleaning_corpus', 'steps') }}
    )
    where rn = 1
),

cleaned as (
    select
        step_id,
        document_id,
        step_order,
        -- Clean step text (trim, normalize whitespace)
        trim(replaceRegexpOne(step_text, '\\s+', ' ')) as step_text,
        step_summary,
        confidence,
        extraction_method,
        created_at
    from source
    where
        -- Filter out invalid steps
        step_id is not null
        and step_id != ''
        and document_id is not null
        and document_id != ''
        and step_order > 0
        and step_text is not null
        and trim(step_text) != ''
),

with_metrics as (
    select
        *,
        -- Step length metrics
        length(step_text) as step_text_length,
        length(step_text) - length(replace(step_text, ' ', '')) + 1 as step_word_count
    from cleaned
)

select * from with_metrics

