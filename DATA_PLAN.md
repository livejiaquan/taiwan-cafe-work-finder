# Data Plan

Last updated: 2026-08-10

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
- `data/raw/manual_cafe_seed.template.csv`
- `data/raw/cafe_conflicts.json`
- `data/raw/source_seed_queries.csv`

## Cafe Record Schema

Each record should contain:

- `cafe_id`: stable project ID, usually derived from source and normalized name/address
- `canonical_name`: cafe name used for display and deduplication
- `aliases`: alternate names or branch labels
- `branch_name`: branch or store name when known
- `branch_identity_status`: `resolved`, `ambiguous`, or `unknown`
- `operational_status`: explicitly observed operating state or `unknown`/`conflicted`
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
- `last_verified_at`: ISO date for a completed record-level verification; never a retrieval date
- `conflicts`: structured, source-linked unresolved or resolved signals
- `notes`: short caveats for manual review

`aliases`, `external_ids`, `notes`, source metadata, claims, confidence, and
conflict workflow fields are internal-only. They must not be rendered directly
by a UI. Nonempty public contact or branch values require fresh matching claims
and must pass the production publication audit. The audit report itself is not
a public feed; a future UI must consume a separate explicit whitelist
projection of publishable records and approved display fields.

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

Confidence is field-specific and does not grant publication by itself. OSM may
have high identity confidence while work conditions remain unknown. Legacy
forum and restricted provider data cannot publish even when a normalized field
has medium/high confidence. Publication requires a fresh matching structured
claim under a reviewed source policy.

## Deduplication Strategy

Records are potential duplicates when:

- normalized names are very similar and coordinates are within 150 meters
- normalized names are very similar and addresses are similar
- the same Google Place ID or OSM ID appears more than once
- one record appears to be a branch-level alias of another

Deduplication should not collapse branches unless source data clearly identifies
the same physical location. The merge command fails closed on any duplicate
`cafe_id`; entity resolution remains a separate reviewed task.

## Source Tracking

Every curated record must include at least one source link. Source entries track:

- `source_id`
- `source_type`
- `url`
- `title`
- `retrieved_at`
- `published_at`
- `source_updated_at`
- reviewed `policy_id`
- `claims` containing canonical field, normalized value, observation date,
  enumerated method, and confidence
- `evidence_fields`
- `confidence`
- `notes`

## Update Workflow

1. Add or refresh raw source files.
2. Run source-specific normalizers.
3. Merge processed outputs; missing/empty inputs and duplicate IDs are errors.
4. Run dataset validation.
5. Run publication readiness with an explicit `--as-of` date.
6. Run duplicate check.
7. Update source, review, and task documentation.

Collectors fail closed: empty, partial, error-marked, or structurally unexpected
provider responses never replace an existing raw snapshot. Successful raw and
generated writes use atomic replacement, preserve the target mode, flush file
content, and sync the parent directory when the platform supports it. A parent
directory sync failure after rename is explicitly reported as an already
replaced target with uncertain durability, never as an untouched output.
