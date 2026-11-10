# language_spread_by_year

Concentration of each language in its communities, year by year (using the global partition).

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (76 rows)

| Column | Meaning |
|---|---|
| `year` | year |
| `language` | code |
| `language_name` | name |
| `channels` | n |
| `communities` | n comm |
| `share_in_largest` | share |
