# community_summary

Quality and size indicators of each partition of the full graph.

## How it was generated

`community_detection_v2.py`, run on 2026-11-08.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (1 rows)

| Column | Meaning |
|---|---|
| `algorithm` | leiden or infomap |
| `n_nodes` | channels in the graph |
| `n_edges_directed` | distinct (origin, destination) pairs |
| `total_forwards` | sum of the weights |
| `n_communities` | number of communities |
| `modularity` | weighted modularity (undirected, A<->B summed) |
| `intra_share` | share of forwards whose origin and destination are in the same community |
| `largest_community` | channels in the largest community |
| `largest_share` | that size / all channels |
| `top10_share` | share of channels in the 10 largest communities |
| `singletons` | communities with a single channel |
| `codelength` | Infomap map equation (bits), empty for Leiden |
| `seconds` | run time |
