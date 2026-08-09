# Tasks

## Phase 1 Checklist

- [x] Define project scope and Phase 1 non-goals.
- [x] Research public and accessible cafe data sources.
- [x] Define canonical cafe schema and work-friendly attributes.
- [x] Create raw, processed, and curated data folders.
- [x] Implement core normalization utilities.
- [x] Implement validation and duplicate detection.
- [x] Implement Overpass collector.
- [x] Implement optional Google Places collector.
- [x] Create curated seed dataset with source links and confidence notes.
- [x] Run tests.
- [x] Validate curated dataset format.
- [x] Check duplicate candidates.
- [x] Document source coverage and limitations.

## Phase 1 Outputs

- Manual curated seed: `data/curated/cafes.seed.jsonl` with 8 records.
- OSM raw sample: `data/raw/overpass_taipei_sample.json` with 2,388 Taipei-area cafe elements.
- OSM normalized sample: `data/processed/osm_cafes.normalized.jsonl` with 2,388 records.
- Source review queue: `data/processed/source_review_queue.csv` with 11 search/source-discovery rows.
- Duplicate report: `data/processed/duplicate_candidates.json`.

## Phase 2 Handoff Candidates

- Design frontend information architecture.
- Define search/filter UX from validated attributes.
- Decide map provider and geocoding strategy.
- Build source transparency UI for confidence and last verified dates.
- Add user feedback/reporting flow for stale cafe rules.
- Add scheduled refresh jobs for API-backed sources.
