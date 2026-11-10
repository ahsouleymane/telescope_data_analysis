# diversity_global

Global language diversity (entropy in bits, normalised entropy, effective number of languages) for all years and, when possible, per year.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (11 rows)

| Column | Meaning |
|---|---|
| `scope` | all / year YYYY |
| `n_languages` | distinct |
| `entropy_bits` | H bits |
| `entropy_normalised` | H / log2(k) |
| `effective_languages_hill2` | 1 / sum p^2 |
