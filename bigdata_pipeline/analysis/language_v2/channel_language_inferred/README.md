# channel_language_inferred

Channels without a detected language for which a language was inferred (winning vote share >= 0.8). These values are guesses ('inferred'), not detections.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (191,621 rows)

| Column | Meaning |
|---|---|
| `channel_id` | Telegram channel id |
| `inferred_language` | guessed language code |
| `vote_share` | share of neighbour forwards coming from that language |
| `neighbour_forwards` | total forwards with neighbours of a known language |
| `source` | always 'inferred' |
