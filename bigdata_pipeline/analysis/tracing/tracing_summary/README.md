# tracing_summary

Headline numbers of the chains after removing duplicated relays (same destination channel and message id).

## How it was generated

`source_tracing_v2.py`, run on 2026-11-11.

Relays: `telescope_pipeline_files/gold/chains` (job 2). Messages: `telescope_pipeline_files/clean_dedup` (job 1).

## Content (13 rows)

| Column | Meaning |
|---|---|
| `measure` | name of the measure |
| `value` | value |
