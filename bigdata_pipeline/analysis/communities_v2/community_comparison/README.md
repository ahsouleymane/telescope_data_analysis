# community_comparison

Agreement between partitions, computed on the channels present in both. leiden_seed_vs_leiden_seed+1 is the same algorithm run twice with different random seeds: it measures how much of the disagreement between two partitions is just algorithm noise.

## How it was generated

`community_detection_v2.py`, run on 2026-11-11.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (2 rows)

| Column | Meaning |
|---|---|
| `pair` | partitions compared |
| `n_common` | channels present in both |
| `nmi` | normalized mutual information (0 = unrelated, 1 = identical) |
| `ari` | adjusted Rand index |
| `homogeneity` | each community of the 2nd partition holds channels of a single community of the 1st (1 = yes) |
| `completeness` | channels of a community of the 1st partition stay together in the 2nd |
