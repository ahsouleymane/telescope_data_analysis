# language_yearly

Year by year: language mix and diversity of the channels active that year, and how much of the forwarding stays inside a language. Years with too few forwards between known-language channels are left out.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (9 rows)

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `active_channels` | channels that forward or are forwarded that year |
| `active_with_language` | of which with a known language |
| `languages` | distinct languages among them |
| `top_language` | most frequent language |
| `top_language_share` | its share of the known active channels |
| `language_entropy_bits` | Shannon entropy of the language mix |
| `effective_languages` | 2^entropy: how many equally frequent languages would give the same diversity |
| `forwards_between_known` | forwards between channels with a known language |
| `same_language_share` | share of those forwards that stay in the language |
| `expected_same_language_share` | same share if language did not matter |
| `assortativity` | 0 = language ignored, 1 = forwards never cross languages |
