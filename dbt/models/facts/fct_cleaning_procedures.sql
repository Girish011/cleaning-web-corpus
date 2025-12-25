{{
    config(
        materialized='table'
    )
}}

with documents as (
    select * from {{ ref('stg_documents') }}
),

steps as (
    select * from {{ ref('stg_steps') }}
),

tools_source as (
    select
        document_id,
        tool_name
    from {{ source('cleaning_corpus', 'tools') }}
    where document_id is not null
    and tool_name is not null
    and tool_name != ''
),

-- Count steps and tools per document
document_metrics as (
    select
        d.document_id,
        d.surface_type,
        d.dirt_type,
        d.cleaning_method,
        d.extraction_confidence,
        d.quality_score,
        d.fetched_at,
        d.processed_at,
        count(distinct s.step_id) as step_count,
        count(distinct t.tool_name) as tool_count
    from documents d
    left join steps s on d.document_id = s.document_id
    left join tools_source t on d.document_id = t.document_id
    group by
        d.document_id,
        d.surface_type,
        d.dirt_type,
        d.cleaning_method,
        d.extraction_confidence,
        d.quality_score,
        d.fetched_at,
        d.processed_at
)

-- Aggregate by (surface_type × dirt_type × cleaning_method) combination
select
    surface_type,
    dirt_type,
    cleaning_method,
    -- Measures
    count(*) as document_count,
    sum(step_count) as total_step_count,
    avg(step_count) as avg_step_count,
    sum(tool_count) as total_tool_count,
    avg(tool_count) as avg_tool_count,
    avg(extraction_confidence) as avg_extraction_confidence,
    avg(quality_score) as avg_quality_score,
    -- Metadata
    min(fetched_at) as first_seen_at,
    max(fetched_at) as last_seen_at,
    count(*) as total_occurrences
from document_metrics
group by
    surface_type,
    dirt_type,
    cleaning_method

