{{
    config(
        materialized='view'
    )
}}

with source as (
    -- Deduplicate by taking the most recent record per document_id
    select *
    from (
        select *,
               row_number() over (partition by document_id order by processed_at desc) as rn
        from {{ source('cleaning_corpus', 'raw_documents') }}
    )
    where rn = 1
),

cleaned as (
    select
        document_id,
        url,
        title,
        main_text,
        raw_html,
        source,
        language,
        http_status,
        fetched_at,
        processed_at,
        -- Normalize surface_type (lowercase, trim)
        lower(trim(surface_type)) as surface_type,
        -- Normalize dirt_type (lowercase, trim)
        lower(trim(dirt_type)) as dirt_type,
        -- Normalize cleaning_method (lowercase, trim, replace spaces with underscores)
        lower(replace(trim(cleaning_method), ' ', '_')) as cleaning_method,
        extraction_method,
        extraction_confidence,
        image_count,
        video_count,
        word_count,
        character_count
    from source
    where
        -- Filter out invalid documents
        document_id is not null
        and document_id != ''
        and url is not null
        and url != ''
        and surface_type is not null
        and surface_type != ''
        and dirt_type is not null
        and dirt_type != ''
        and cleaning_method is not null
        and cleaning_method != ''
)

select
    *,
    -- Computed fields
    case when word_count > 0 then 1 else 0 end as has_content,
    case when image_count > 0 then 1 else 0 end as has_images,
    case when extraction_confidence is not null and extraction_confidence >= 0.5 then 1 else 0 end as has_high_confidence,
    -- Simple quality score (0-1) based on word count and confidence
    case
        when word_count >= 1000 and extraction_confidence >= 0.7 then 1.0
        when word_count >= 500 and extraction_confidence >= 0.5 then 0.8
        when word_count >= 200 and extraction_confidence >= 0.3 then 0.6
        when word_count >= 100 then 0.4
        else 0.2
    end as quality_score
from cleaned

