# language_yearly_by_language

Year by year, for the eight languages that forward the most: their weight and cohesion.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (65 rows)

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `language` | code |
| `language_name` | name |
| `active_channels` | active channels with this language |
| `share_of_active` | share of the known active channels |
| `forwards_out` | forwards of the language's content that year (both languages known) |
| `same_language_share` | share of them received by the same language |
| `lift` | observed / expected |
