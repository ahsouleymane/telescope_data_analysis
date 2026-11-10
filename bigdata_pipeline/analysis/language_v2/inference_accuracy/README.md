# inference_accuracy

Accuracy of the neighbour-vote language guess, measured by hiding 10% of the known languages. Compare with the baseline of always predicting the most frequent language.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (7 rows)

| Column | Meaning |
|---|---|
| `row` | bin of winning vote share |
| `vote_share_from` | bin lower bound |
| `vote_share_to` | bin upper bound |
| `held_out_channels` | hidden channels in the bin |
| `accuracy` | share guessed right |
| `baseline_majority_language` | accuracy of always guessing the most frequent language |
| `held_out_total` | hidden channels in total |
| `with_known_neighbour` | hidden channels having at least one neighbour with a known language |
