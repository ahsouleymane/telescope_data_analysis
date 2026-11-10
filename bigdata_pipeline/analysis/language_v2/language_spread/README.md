# language_spread

For each language with at least 50 channels: how many communities it is spread over.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (15 rows)

| Column | Meaning |
|---|---|
| `language` | code |
| `language_name` | name |
| `channels` | channels with this language |
| `communities` | communities containing at least one |
| `largest_community` | community with most of them |
| `share_in_largest` | share of its channels in that community |
| `communities_for_80pct` | communities needed to cover 80% of its channels |
