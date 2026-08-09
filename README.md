# Taiwan Cafe Work Finder

Phase 1 builds the research and data-collection foundation for a future Taiwan work-friendly cafe discovery product.

This repository currently does not build the final website. It focuses on source research, data schema, collectors, normalization, validation, deduplication, and a curated seed dataset.

## Structure

- `data/raw/`: source snapshots, manual seed CSVs, and source discovery queries
- `data/processed/`: generated normalized JSONL and duplicate/source-review outputs
- `data/curated/`: curated seed dataset for future product work
- `scripts/collectors/`: public/API source collectors and source queue tooling
- `scripts/normalize/`: normalization, merge, validation, and duplicate checks
- `src/cafe_work_finder/`: shared schema, normalization, IO, and dedupe code
- `docs/`: schema and implementation planning docs

## Quick Start

Run unit tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Normalize the manual seed dataset:

```bash
PYTHONPATH=src python scripts/normalize/normalize_manual.py
```

Build the manual source review queue:

```bash
python scripts/collectors/build_source_queue.py
```

Run Overpass collector dry-run:

```bash
python scripts/collectors/collect_overpass.py --dry-run
```

If network access is available, collect Overpass data:

```bash
python scripts/collectors/collect_overpass.py
PYTHONPATH=src python scripts/normalize/normalize_osm.py
```

Run Google Places collector dry-run:

```bash
python scripts/collectors/collect_google_places.py --dry-run
```

If `GOOGLE_MAPS_API_KEY` is set and billing/API access is configured:

```bash
GOOGLE_MAPS_API_KEY=... python scripts/collectors/collect_google_places.py
PYTHONPATH=src python scripts/normalize/normalize_google_places.py
```

Merge curated seed records:

```bash
PYTHONPATH=src python scripts/normalize/merge_curated.py --manual-only
```

Validate curated data:

```bash
PYTHONPATH=src python scripts/normalize/validate_dataset.py
```

Check likely duplicates:

```bash
PYTHONPATH=src python scripts/normalize/find_duplicates.py
```

## Source Policy

Allowed:

- official APIs
- public pages that are manually reviewable
- OpenStreetMap / Overpass
- manually entered source links
- official cafe websites and public social links when accessible

Not allowed:

- bypassing login, paywalls, CAPTCHAs, or private content
- scraping Instagram or Threads through unofficial APIs
- using proxies or anti-bot circumvention
- bulk-copying copyrighted article content
- presenting stale forum/blog claims as current without verification dates

## Current Outputs

After running the Phase 1 pipeline, expect:

- `data/processed/manual_cafes.normalized.jsonl`
- `data/raw/overpass_taipei_sample.json`
- `data/processed/osm_cafes.normalized.jsonl`
- `data/processed/source_review_queue.csv`
- `data/curated/cafes.seed.jsonl`
- `data/processed/duplicate_candidates.json`

Current generated counts:

- 8 manually curated seed records
- 2,388 raw Overpass cafe elements for the Taipei-area sample
- 2,388 normalized OSM records
- 11 manually reviewable source-discovery queries

The curated seed is intentionally smaller than the OSM processed dataset. OSM is broad coverage; curated records require work-friendly source evidence.

## Phase 2 Handoff

Phase 2 should design the product/frontend around the validated schema:

- search and filters for work-friendly attributes
- source transparency and confidence labels
- map/list UX
- stale-data reporting
- city/district expansion
- scheduled API/manual refresh process
