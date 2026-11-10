# language_top_channels

The 10 most forwarded channels of each of the 12 largest languages.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (120 rows)

| Column | Meaning |
|---|---|
| `language` | code |
| `language_name` | name |
| `rank` | rank inside the language |
| `channel_id` | Telegram channel id |
| `community` | its Leiden community |
| `times_forwarded` | times its content was forwarded |
| `forwards_made` | forwards it made |
