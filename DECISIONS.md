# Decisions

## 2026-06-01: Phase 1 Scope

Decision: Phase 1 is limited to research, source strategy, data schema, collection scripts, normalization, validation, deduplication, curated seed data, and documentation.

Reason: The project needs a reliable data foundation before product UI decisions. Work-friendly cafe discovery depends on source quality and update processes, not only interface design.

## 2026-06-01: Dataset Format

Decision: Use JSON Lines for curated and processed datasets.

Reason: JSONL is easy to diff, append, validate, stream, and inspect manually. It also keeps each cafe as an independent record.

## 2026-06-01: Source Ethics

Decision: Do not automate Instagram, Threads, login-gated Dcard features, CAPTCHA-protected pages, paywalled pages, or anti-bot-protected content.

Reason: Phase 1 should be reproducible and respectful of platform restrictions. Unsafe sources are documented as manual/optional.

## 2026-06-01: Structured API Priority

Decision: Use Overpass as the first automated source and Google Places as optional API enrichment when a key is available.

Reason: Overpass is public and reproducible. Google Places is valuable but depends on API access, billing, and field masks.

## 2026-06-01: Confidence Model

Decision: Store confidence at both overall-record and field levels.

Reason: A cafe can have high confidence for coordinates from OSM but low confidence for quietness from a single old forum post.

## 2026-06-01: Curated Seed Versus Processed OSM

Decision: Keep `data/curated/cafes.seed.jsonl` to manually reviewed seed records, while storing the larger Overpass pull in `data/processed/osm_cafes.normalized.jsonl`.

Reason: OSM gives valuable coverage but does not usually prove work-friendly attributes. Treating all OSM POIs as curated would overstate confidence for the final product.
