# language_homophily

For each origin language: share of its forwards received by channels of the same language, versus the share expected if forwards ignored language (= share of all forwards received by that language).

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (47 rows)

| Column | Meaning |
|---|---|
| `language` | code |
| `language_name` | name |
| `forwards_out` | forwards written about channels of this language |
| `forwards_in` | forwards received by channels of this language |
| `same_language_share` | share of forwards_out that land in the same language |
| `expected_share` | same share if language did not matter |
| `lift` | observed / expected |
| `audience_entropy_bits` | entropy of the languages that forward this language's content (0 = one language only) |
| `audience_effective_languages` | 2^entropy: effective number of languages in its audience |
