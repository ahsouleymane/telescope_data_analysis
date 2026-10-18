# Charts — Community diffusion maps

All PNG maps produced by `community_diffusion_maps.py`.

- `fig_community_map_global.png` — 2x5 grid, one panel per year (2015-2024), all on the same fixed layout.
- `fig_community_map_2015.png` … `fig_community_map_2024.png` — one full-size map per year, same fixed layout as the grid.

Legend: `#rank Language (share%, n=known/total)` (rank = position in `community_sizes.csv`, #1 = largest).
Node size = that period's diffusion activity; edge width = that period's cross-community cascades. Each panel is normalized to its own period's maximum (sizes are NOT comparable across years).

Coverage note: 2015 and 2024 are partial years in the data (2015-09-29 to 2024-09-28); only ~68% of cascades have a known date.
