# Taiwan Cafe Work Finder

This repository is building an evidence-first cafe finder for quiet solo work or
study in greater Taipei. It is currently a data and trust foundation, not a
public website.

This repository focuses on source research, data schema, collectors, normalization, validation, deduplication, and a curated seed dataset. It also includes a deliberately bounded public-status frontend: it communicates the current verification gate without exposing candidate records as recommendations.

## Structure

- `data/raw/`: source snapshots, manual seed CSVs, and source discovery queries
- `data/processed/`: generated normalized JSONL and duplicate/source-review outputs
- `data/curated/`: curated seed dataset for future product work
- `scripts/collectors/`: public/API source collectors and source queue tooling
- `scripts/normalize/`: normalization, safe merge, validation, and duplicate checks
- `scripts/quality/`: publication-readiness checks that quarantine unsafe candidates
- `src/cafe_work_finder/`: shared schema, normalization, IO, and dedupe code
- `docs/`: schema and implementation planning docs

## Quick Start

Run the public-status frontend:

```bash
npm install
npm run dev
```

The UI is a static Vite + React status and methodology page. It does not read or
ship canonical JSONL, audit output, candidate names, or discovery data. The
search controls remain visibly disabled until a separate whitelist-based public
projection exists and the publication gate is met.

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

Google Places full-content persistence is not part of the production plan. The
collector remains a dry-run/reference path until storage, display, and
attribution policies are redesigned and reviewed.

Merge curated seed records:

```bash
PYTHONPATH=src python scripts/normalize/merge_curated.py
```

Validate curated data:

```bash
PYTHONPATH=src python scripts/normalize/validate_dataset.py
```

Audit the actual publication contract with an explicit date:

```bash
PYTHONPATH=src python scripts/quality/audit_publication_readiness.py --as-of 2026-08-09
```

The expected result for the current eight legacy candidates is `0 publishable`.
They have provenance, but no current observation or branch-level verification.

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

The curated seed is intentionally smaller than the OSM processed dataset. OSM
is a discovery input and is excluded from the default merge. Presence in the
curated file still does not imply publication readiness.

## Current Roadmap

The trust contract and evidence-based product roadmap are in
[`docs/data-publication-contract.md`](docs/data-publication-contract.md) and
[`docs/product/mission-roadmap.md`](docs/product/mission-roadmap.md). A thin
mobile product starts only after 10-12 branch-resolved cafes meet that contract.
The 2026-08-11 [MVP browse/find readiness decision](docs/research/2026-08-11-mvp-browse-find-readiness.md)
confirms the current result is still `0 publishable`; the next step is a private
three-branch verification-operations pilot, not an empty or sample-data UI.
