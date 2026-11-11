# community_names

Name of each Leiden community: '<Language> (<share>%, n=<known>/<size>)', with fewer than 3 known channels the name is flagged low confidence; no known channel gives 'Unknown (0 known)'. Languages from `telescope_files/Channel_Language.csv`.

## How it was generated

`community_detection_v2.py`, run on 2026-11-11.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (822 rows)

| Column | Meaning |
|---|---|
| `community` | community number (0 = largest) |
| `community_name` | label built from the dominant language |
| `dominant_language` | language with most channels among those with a known language |
| `dominant_share` | its share among the channels with a known language |
| `n_known` | channels of the community with a known language |
| `size` | channels in the community |
