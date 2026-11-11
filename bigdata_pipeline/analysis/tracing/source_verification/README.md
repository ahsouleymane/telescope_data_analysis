# source_verification

Is the source of a relay present in the dataset, and does the header date agree with the post found?

## How it was generated

`source_tracing_v2.py`, run on 2026-11-11.

Relays: `telescope_pipeline_files/gold/chains` (job 2). Messages: `telescope_pipeline_files/clean_dedup` (job 1).

## Content (7 rows)

| Column | Meaning |
|---|---|
| `measure` | check |
| `original_posts` | distinct original posts |
| `share_of_posts` | share of posts |
| `relays` | relays of those posts |
| `share_of_relays` | share of relays |
| `meaning` | reading |
