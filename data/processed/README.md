# Processed Data

This folder stores generated intermediate outputs.

Typical files:

- `manual_cafes.normalized.jsonl`
- `osm_cafes.normalized.jsonl`
- `google_places.normalized.jsonl`
- `source_review_queue.csv`
- `duplicate_candidates.json`

Files here can be regenerated from `data/raw/` and scripts.

`retrieved_at` is copied from the raw snapshot. Regenerating an old snapshot
must not change it to the current date or manufacture `observed_at` or
`last_verified_at`. OSM and Google Places outputs are discovery candidates, not
default curated recommendations.
