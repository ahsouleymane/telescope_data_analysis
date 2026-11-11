# delay_by_year

Speed of relaying by year of the relay.

## How it was generated

`source_tracing_v2.py`, run on 2026-11-11.

Relays: `telescope_pipeline_files/gold/chains` (job 2). Messages: `telescope_pipeline_files/clean_dedup` (job 1).

## Content (10 rows)

| Column | Meaning |
|---|---|
| `year` | year of the relay |
| `relays` | relays |
| `median_delay_s` | median delay in seconds |
| `share_within_1h` | relays within one hour of the original |
| `share_within_1day` | within one day |
