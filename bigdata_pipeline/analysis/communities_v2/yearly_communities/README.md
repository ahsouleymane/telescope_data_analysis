# yearly_communities

One Leiden partition per year (same parameters) and its similarity to the previous year.

## How it was generated

`community_detection_v2.py`, run on 2026-11-11.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (8 rows)

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `n_channels` | channels with a link that year |
| `n_edges` | distinct pairs that year |
| `n_forwards` | forwards that year |
| `n_communities` | Leiden communities that year |
| `modularity` | modularity of that year's partition |
| `largest_share` | share of channels in the largest community |
| `n_common_prev` | channels present this year and the previous one |
| `nmi_prev` | NMI with the previous year |
| `ari_prev` | ARI with the previous year |
| `nmi_other_seed` | NMI between two Leiden runs of the SAME year with different random seeds (noise floor) |
