# activity_by_language

Forwards sent and received per language, and the same per channel. Uses only channels with a known language.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (48 rows)

| Column | Meaning |
|---|---|
| `language` | code |
| `language_name` | name |
| `channels_with_language` | n |
| `forwards_sent` | sent |
| `forwards_received` | recv |
| `forwards_sent_per_channel` | sent/n |
| `forwards_received_per_channel` | recv/n |
