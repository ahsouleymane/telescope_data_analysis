# top_origin_posts

The 100 most relayed original posts.

## How it was generated

`source_tracing_v2.py`, run on 2026-11-11.

Relays: `telescope_pipeline_files/gold/chains` (job 2). Messages: `telescope_pipeline_files/clean_dedup` (job 1).

## Content (100 rows)

| Column | Meaning |
|---|---|
| `origin_channel` | source channel |
| `origin_post` | post id |
| `relays` | number of relays |
| `first_relay_delay_s` | delay of the first relay (s) |
| `last_relay_delay_s` | delay of the last relay (s) |
