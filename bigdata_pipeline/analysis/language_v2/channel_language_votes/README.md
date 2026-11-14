# channel_language_votes

Channels that have NO language in Channel_Language.csv and none in channel_language_inferred: at least one forwarding partner has a known language, but no language reaches the minimum vote share (0.8). For each, the three best-voted languages with their share of the neighbour forwards. A mixed audience shows up as several shares of similar size. Channels with no partner of a known language are not listed (nothing to vote on). Only languages with at least 50 known channels take part in the vote.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-14.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (4,412 rows)

| Column | Meaning |
|---|---|
| `channel_id` | Telegram channel id |
| `n_voting_languages` | number of languages with at least one vote |
| `language_1` | best-voted language code |
| `share_1` | its share of the neighbour forwards |
| `language_2` | second language code (empty if none) |
| `share_2` | its share |
| `language_3` | third language code (empty if none) |
| `share_3` | its share |
| `share_other` | share of the remaining languages (1 - share_1 - share_2 - share_3) |
| `neighbour_forwards` | total forwards with neighbours of a known language |
