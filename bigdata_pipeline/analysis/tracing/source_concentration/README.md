# source_concentration

Share of relays held by the largest source channels.

## How it was generated

`source_tracing_v2.py`, run on 2026-11-11.

Relays: `telescope_pipeline_files/gold/chains` (job 2). Messages: `telescope_pipeline_files/clean_dedup` (job 1).

## Content (6 rows)

| Column | Meaning |
|---|---|
| `top_share_of_sources` | fraction of source channels (largest first) |
| `sources` | number of channels |
| `share_of_relays` | share of all relays they hold |
