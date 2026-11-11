# delay_distribution

Delay between the original post and its relays, for all relays and for the first relay of each post.

## How it was generated

`source_tracing_v2.py`, run on 2026-11-11.

Relays: `telescope_pipeline_files/gold/chains` (job 2). Messages: `telescope_pipeline_files/clean_dedup` (job 1).

## Content (8 rows)

| Column | Meaning |
|---|---|
| `delay_class` | delay range |
| `relays` | relays |
| `share_of_relays` | share of relays |
| `first_relays` | first relays of posts |
| `share_of_first_relays` | share of posts |
