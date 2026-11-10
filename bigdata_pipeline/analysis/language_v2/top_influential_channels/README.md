# top_influential_channels

Top 5 channels by forwards received, per language, joined with channel_stats if available.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (175 rows)

| Column | Meaning |
|---|---|
| `language` | code |
| `language_name` | name |
| `rank` | rank |
| `channel_id` | channel |
| `forwards_received` | recv |
