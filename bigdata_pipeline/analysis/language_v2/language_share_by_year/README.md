# language_share_by_year

Share of each language among channels, year by year (computed on all channels of the year's forward graph that have a known language).

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (262 rows)

| Column | Meaning |
|---|---|
| `year` | year |
| `language` | code |
| `language_name` | name |
| `channels` | n |
| `share` | share within year |
