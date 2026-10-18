# Community names (dominant language)

One row per community, giving its human-readable name.

- `community_id`: the Leiden community ID.
- `community_name`: a label built from the dominant language
  among channels with a known language.

Naming rules:
- Fewer than 3 known-language channels:
  `Unknown (low confidence: <Lang>? n=known/total)`.
- Zero known-language channels: `Unknown (0 known)`.
- Otherwise: `<Language> (<share>%, n=known/total)`.

## File
- `community_names.csv` — 677 rows, 2 columns.

## Columns
- `community_id` (int64) — e.g. `6`
- `community_name` (str) — e.g. `Persian (81%, n=2812/8292)`
