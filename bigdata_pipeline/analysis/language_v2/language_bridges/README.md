# language_bridges

Channels with the most forwards across a language boundary: 'exports' = their content is forwarded by channels of another language; 'imports' = they forward content written by channels of another language. Only forwards where both channels have a known language are counted.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (60 rows)

| Column | Meaning |
|---|---|
| `direction` | exports or imports |
| `rank` | rank inside the direction |
| `channel_id` | Telegram channel id |
| `language` | its language code |
| `language_name` | name |
| `community` | its Leiden community |
| `forwards_with_known_language` | its forwards in this direction with a known language on both sides |
| `forwards_across_languages` | of which across a language boundary |
| `cross_share` | ratio of the two |
| `main_other_language` | the foreign language involved most often |
