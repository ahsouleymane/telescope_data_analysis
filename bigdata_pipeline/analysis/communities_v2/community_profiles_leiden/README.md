# community_profiles_leiden

One row per Leiden community: size, forwards leaving, entering and staying inside, and the five most connected channels.

## How it was generated

`community_detection_v2.py`, run on 2026-11-11.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (822 rows)

| Column | Meaning |
|---|---|
| `community` | community number |
| `size` | channels |
| `forwards_out` | forwards written by its channels |
| `forwards_in` | forwards made by its channels |
| `forwards_inside` | forwards from and to the same community |
| `inside_share_of_out` | forwards_inside / forwards_out |
| `top_channels` | five channels with the most forwards (in+out) |
