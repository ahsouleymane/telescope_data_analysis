# language_neighbour_diversity

Entropy of the languages of each language's outgoing and incoming neighbours. `lift_vs_global` = neighbour entropy / global entropy: < 1 means the language sits in a linguistically narrow neighbourhood, > 1 means its neighbourhood is more diverse than the graph.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (15 rows)

| Column | Meaning |
|---|---|
| `language` | code |
| `language_name` | name |
| `out_forwards` | out n |
| `in_forwards` | in n |
| `neighbour_languages_out` | n out |
| `neighbour_languages_in` | n in |
| `entropy_out_bits` | H out |
| `entropy_in_bits` | H in |
| `entropy_out_lift_vs_global` | lift out |
| `entropy_in_lift_vs_global` | lift in |
