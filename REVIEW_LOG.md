# Review Log

## 2026-06-01 Initial Phase 1 Review

Scope reviewed:

- project is currently empty
- Git repository root is `/Users/jiaquan/Development`, not this subfolder
- no existing frontend or backend exists in `taiwan-cafe-work-finder`
- final UI is explicitly out of scope

Initial source review:

- Overpass is safe for automated collection of structured cafe POIs.
- Google Places requires an API key and field-mask-aware requests.
- Dcard, PTT, blogs, and travel sites are useful for work-friendly claims but require manual review and source-date tracking.
- Instagram and Threads should remain manual/optional unless official API permissions are available.

Verification to complete before stopping:

- run unit tests
- run a collector or dry-run where network/API access is unavailable
- validate curated JSONL
- check duplicate candidates
- update task checklist

## 2026-06-01 Phase 1 Verification Results

Commands run:

- `PYTHONPATH=src python -m unittest discover -s tests -v`
- `PYTHONPATH=src python scripts/normalize/normalize_manual.py`
- `python scripts/collectors/build_source_queue.py`
- `python scripts/collectors/collect_overpass.py --dry-run`
- `python scripts/collectors/collect_google_places.py --dry-run`
- `python scripts/collectors/collect_overpass.py`
- `PYTHONPATH=src python scripts/normalize/normalize_osm.py`
- `PYTHONPATH=src python scripts/normalize/merge_curated.py --manual-only`
- `PYTHONPATH=src python scripts/normalize/validate_dataset.py`
- `PYTHONPATH=src python scripts/normalize/find_duplicates.py`

Results:

- Unit tests passed: 4 tests.
- Manual normalizer wrote 8 records.
- Source queue builder wrote 11 review rows.
- Overpass dry-run wrote a reproducible query.
- Live Overpass collection initially failed inside the sandbox with DNS/network resolution error, then succeeded with approved network access.
- Live Overpass collection wrote 2,388 raw cafe elements to `data/raw/overpass_taipei_sample.json`.
- OSM normalizer wrote 2,388 processed records to `data/processed/osm_cafes.normalized.jsonl`.
- Curated seed merge wrote 8 manually reviewed source-linked records to `data/curated/cafes.seed.jsonl`.
- Curated dataset validation passed for 8 records.
- Duplicate check found 0 duplicate candidates in the curated seed.
- Google Places dry-run produced a valid request body and field mask.
- Google Places live collection was skipped because `GOOGLE_MAPS_API_KEY` is not set.

Limitations:

- The curated seed remains small by design; it is human-reviewed and source-linked.
- The OSM sample is broad but not curated; work-friendly attributes are mostly unknown and require enrichment.
- Manual records from Dcard/PTT/blog-style sources need current re-verification before being shown as product truth.
- Chain/branch records require branch-level verification before frontend use.

## 2026-08-11 Trust Foundation Correction

The 2026-06-01 Google note above is retained as historical execution context,
not current product guidance. A missing API key was why that run did not make a
live request, but it is not the durable blocker. The live collector is now
policy-disabled because the previous full-response persistence and normalized
snapshot design lacks an approved storage, display, and attribution contract.
The dry-run remains only as a request/reference check.

The committed 2,388-element Overpass snapshot contains zero element
`timestamp` and zero `version` fields. The current collector/query requests
`out meta` for future refreshes, but documentation and publication checks must
not imply that the legacy snapshot already carries that metadata. Even when
present, an OSM edit timestamp is source lineage rather than a field observation
or verification date.
