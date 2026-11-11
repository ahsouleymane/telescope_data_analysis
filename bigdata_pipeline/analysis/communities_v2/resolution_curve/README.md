# resolution_curve

Leiden run at several resolutions on the same graph: how the partition coarsens or splits.

## How it was generated

`community_detection_v2.py`, run on 2026-11-11.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (6 rows)

| Column | Meaning |
|---|---|
| `resolution` | Leiden resolution parameter |
| `n_communities` | number of communities |
| `modularity` | modularity of the partition (standard definition, resolution 1) |
| `intra_share` | share of forwards inside communities |
| `largest_share` | share of channels in the largest community |
| `seconds` | run time (empty for the resolution already computed) |
