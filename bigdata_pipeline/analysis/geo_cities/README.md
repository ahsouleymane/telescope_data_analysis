# Theme 4, step 1 - city of each channel

Methods (field `method` in channel_geo)
- direct_channel_language: a city of the channel's language (Channel_Language.csv) is named in its
  title, then description, then username. The first field with a match decides.
- direct_title_language: same search, but with the language the title is written in (script and
  distinctive letters), for channels without a language or with nothing found in their own language.
- neighbours: city taken from the forwarding partners (weighted vote on the forward graph, restricted
  to the countries of the channel's language when known). Accuracy: see propagation_accuracy.

Tables
- channel_geo: final table, one row per channel with a city; `confidence` is 1 for a single direct
  match, 1/n when n cities were found, and the vote share for neighbours.
- channel_city: direct matches, one row per (channel, city). channel_city_inferred: neighbour votes.
- city_coverage, language_coverage (share of channels with a city per language), geo_summary.
- validation_sample: up to 70 random single-city channels per method, to check by hand
  (fill `correct` with 1/0; precision of a method = mean of `correct`).

Timezone step (optional, only if the hours of Temporal_Channel_Metadata.csv are UTC)
- timezone_check: pooled daily peak per city; the file is UTC if the peak moves with the city's UTC offset.
  If the verdict is not UTC (local time, or not enough cities with different offsets) the whole step is skipped.
- When UTC: each channel gets an estimated UTC offset (calibrated on channels with a known city); channel_geo
  shows `tz_consistent` (city offset within 2 h of the estimate) - an independent check of the city; and the
  neighbour vote only considers cities in the channel's time zone (propagation_accuracy compares both variants).
  City offsets are standard time (no daylight saving), so +/-1 h of noise is normal.

Limits: a channel whose text names no city and has no labelled neighbour gets no city; a city name can be a
common word or a person; the language written in the title may differ from the channel's audience;
multi-country languages (en, es, pt, fr, ar) get cities from several countries.
