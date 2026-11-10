# diversity_summary

Summary of the per-community language entropy already in community_language_purity.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (1 rows)

| Column | Meaning |
|---|---|
| `communities_with_language` | communities_with_language |
| `entropy_mean_unweighted` | entropy_mean_unweighted |
| `entropy_mean_weighted` | entropy_mean_weighted |
| `entropy_median` | entropy_median |
| `entropy_max` | entropy_max |
| `share_communities_single_language` | share_communities_single_language |
