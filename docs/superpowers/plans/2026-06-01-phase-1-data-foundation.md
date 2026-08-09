# Phase 1 Data Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable research and data-collection foundation for Taiwan work-friendly cafe discovery without building the final website.

**Architecture:** Use small Python standard-library modules for schema defaults, normalization, validation, and deduplication. Keep source-specific collectors under `scripts/collectors/`, source-specific normalizers under `scripts/normalize/`, raw source snapshots under `data/raw/`, generated intermediates under `data/processed/`, and manually reviewed outputs under `data/curated/`.

**Tech Stack:** Python 3 standard library, JSON Lines, CSV, Markdown documentation, Overpass API, optional Google Places API.

---

### Task 1: Core Data Model

**Files:**
- Create: `src/cafe_work_finder/__init__.py`
- Create: `src/cafe_work_finder/schema.py`
- Test: `tests/test_pipeline.py`

- [ ] Write tests for required record fields and enum validation.
- [ ] Run `python -m unittest discover -s tests -v` and verify the tests fail because the package does not exist yet.
- [ ] Implement schema constants and validation helpers.
- [ ] Run tests again and confirm schema tests pass.

### Task 2: Manual Source Normalization

**Files:**
- Create: `src/cafe_work_finder/normalize.py`
- Create: `data/raw/manual_cafe_seed.csv`
- Create: `scripts/normalize/normalize_manual.py`
- Test: `tests/test_pipeline.py`

- [ ] Write tests for converting a manual CSV row into canonical JSONL shape.
- [ ] Run tests and verify failure for missing normalization implementation.
- [ ] Implement manual row normalization.
- [ ] Add a seed CSV with source URLs and confidence notes.
- [ ] Run the manual normalizer to produce `data/processed/manual_cafes.normalized.jsonl`.

### Task 3: Deduplication

**Files:**
- Create: `src/cafe_work_finder/dedupe.py`
- Create: `scripts/normalize/find_duplicates.py`
- Test: `tests/test_pipeline.py`

- [ ] Write tests for duplicate detection using shared IDs and nearby similar names.
- [ ] Run tests and verify failure for missing dedupe implementation.
- [ ] Implement duplicate candidate detection.
- [ ] Run duplicate check against curated data after merge.

### Task 4: Collectors

**Files:**
- Create: `scripts/collectors/collect_overpass.py`
- Create: `scripts/collectors/collect_google_places.py`
- Create: `scripts/collectors/build_source_queue.py`
- Create: `data/raw/source_seed_queries.csv`
- Create: `data/raw/overpass_taipei_query.overpassql`

- [ ] Implement Overpass query generation and response saving.
- [ ] Implement Google Places Text Search collector that exits clearly when `GOOGLE_MAPS_API_KEY` is missing.
- [ ] Implement source queue builder that creates manually reviewable search URLs.
- [ ] Run dry-run commands for collectors.

### Task 5: Merge, Validate, And Document

**Files:**
- Create: `scripts/normalize/merge_curated.py`
- Create: `scripts/normalize/validate_dataset.py`
- Modify: `README.md`
- Modify: `TASKS.md`
- Modify: `REVIEW_LOG.md`

- [ ] Merge normalized manual and API records into `data/curated/cafes.seed.jsonl`.
- [ ] Validate required fields, enum values, URLs, coordinates, and source links.
- [ ] Run duplicate detection.
- [ ] Update README instructions, task statuses, source coverage, limitations, and Phase 2 next steps.

