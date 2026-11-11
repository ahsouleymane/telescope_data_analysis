# community_language_purity

For each community: dominant language among its channels with a known language, and how pure it is.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (822 rows)

| Column | Meaning |
|---|---|
| `community` | community number (0 = largest) |
| `size` | channels in the community |
| `known_language` | channels with a known language |
| `known_share` | known_language / size |
| `dominant_language` | most frequent language code |
| `dominant_name` | its name |
| `purity` | share of the dominant language among known channels |
| `entropy_bits` | Shannon entropy of the language mix (0 = single language) |
| `n_languages` | distinct languages present |
