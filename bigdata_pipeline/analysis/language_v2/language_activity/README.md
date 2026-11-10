# language_activity

Activity and influence of each language: how much its channels are forwarded, compared with how many channels it has.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (48 rows)

| Column | Meaning |
|---|---|
| `language` | code |
| `language_name` | name |
| `channels` | channels with this language in the graph |
| `share_of_channels` | share of the channels with a known language |
| `times_forwarded` | times the content of these channels was forwarded |
| `share_of_times_forwarded` | its share of all |
| `influence_ratio` | share of forwards received / share of channels (above 1 = more influential than its size) |
| `forwarded_per_channel` | times_forwarded / channels |
| `forwards_made` | forwards these channels made |
| `messages` | messages written (from channel_stats) |
| `messages_per_channel` | messages / channels |
