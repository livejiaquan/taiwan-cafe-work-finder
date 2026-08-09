# Data Plan

## Canonical Dataset Format

The canonical cafe dataset is JSON Lines:

- one cafe record per line
- UTF-8 encoded
- stable field names
- explicit source links per record
- source-specific confidence per field where practical

Primary curated output:

- `data/curated/cafes.seed.jsonl`

Generated intermediate outputs:

- `data/processed/manual_cafes.normalized.jsonl`
- `data/processed/osm_cafes.normalized.jsonl`
- `data/processed/google_places.normalized.jsonl`

Raw source snapshots:

- `data/raw/overpass_*.json`
- `data/raw/google_places_*.json`
- `data/raw/manual_cafe_seed.csv`
- `data/raw/source_seed_queries.csv`

## Cafe Record Schema

Each record should contain:

- `cafe_id`: stable project ID, usually derived from source and normalized name/address
- `canonical_name`: cafe name used for display and deduplication
- `aliases`: alternate names or branch labels
- `branch_name`: branch or store name when known
- `city`: Taiwan city/county
- `district`: district/township when known
- `address`: street address when known
- `coordinates`: `lat` and `lng`, nullable if unverified
- `external_ids`: Google Place ID, OSM type/ID, website handles, or other durable IDs
- `contact`: website, phone, Instagram, Facebook, Threads, Google Maps URL, and other social links
- `work_attributes`: work-friendly attributes with normalized values
- `source_links`: source URLs and metadata used for the record
- `field_confidence`: confidence per high-value attribute
- `overall_confidence`: `high`, `medium`, `low`, or `unknown`
- `last_verified_at`: ISO date for the newest source/manual verification
- `notes`: short caveats for manual review

## Work-Friendly Attributes

Normalized work attributes:

- `unlimited_time`: `yes`, `no`, `limited`, `conditional`, `unknown`
- `outlets`: `abundant`, `some`, `limited`, `none`, `unknown`
- `wifi`: `yes`, `no`, `unknown`
- `quietness`: `quiet`, `moderate`, `lively`, `noisy`, `unknown`
- `seat_comfort`: `good`, `fair`, `poor`, `unknown`
- `solo_work_suitability`: `high`, `medium`, `low`, `unknown`
- `meeting_suitability`: `high`, `medium`, `low`, `unknown`
- `study_suitability`: `high`, `medium`, `low`, `unknown`
- `online_meeting_suitability`: `high`, `medium`, `low`, `unknown`
- `long_stay_suitability`: `high`, `medium`, `low`, `unknown`
- `opening_hours`: free text from source/API
- `minimum_order`: free text
- `price_level`: Google-style numeric/string or manual free text
- `food_available`: `yes`, `no`, `unknown`
- `reservation`: `yes`, `no`, `unknown`

## Confidence Rules

- `high`: official cafe site, Google Places, OSM with coordinates, or multiple recent independent sources agree.
- `medium`: one recent public article/forum post gives concrete details such as hours, outlets, Wi-Fi, and minimum order.
- `low`: older article/forum mention, incomplete address/branch, or single user-generated source.
- `unknown`: imported structured POI with no work-friendly evidence yet.

## Deduplication Strategy

Records are potential duplicates when:

- normalized names are very similar and coordinates are within 150 meters
- normalized names are very similar and addresses are similar
- the same Google Place ID or OSM ID appears more than once
- one record appears to be a branch-level alias of another

Deduplication should not collapse branches unless source data clearly identifies the same physical location.

## Source Tracking

Every curated record must include at least one source link. Source entries track:

- `source_id`
- `source_type`
- `url`
- `title`
- `retrieved_at`
- `published_at`
- `evidence_fields`
- `confidence`
- `notes`

## Update Workflow

1. Add or refresh raw source files.
2. Run source-specific normalizers.
3. Merge processed outputs.
4. Run dataset validation.
5. Run duplicate check.
6. Update `SOURCE_RESEARCH.md`, `REVIEW_LOG.md`, and `TASKS.md`.

