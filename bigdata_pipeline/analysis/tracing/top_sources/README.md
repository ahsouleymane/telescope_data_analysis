# top_sources

The 50 most relayed source channels.

## How it was generated

`source_tracing_v2.py`, run on 2026-11-11.

Relays: `telescope_pipeline_files/gold/chains` (job 2). Messages: `telescope_pipeline_files/clean_dedup` (job 1).

## Content (50 rows)

| Column | Meaning |
|---|---|
| `origin_channel` | source channel id |
| `original_posts` | its posts that were relayed |
| `relays` | relays of its posts |
| `relaying_channels` | distinct channels that relayed it |
| `relays_per_post` | relays / posts |
| `share_of_relays` | share of all relays |
| `language` | language from Channel_Language.csv |
