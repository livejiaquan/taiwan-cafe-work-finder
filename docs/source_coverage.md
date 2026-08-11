# Source Coverage

Generated: 2026-06-01

## Automated Sources

| Source | File | Count | Status | Notes |
| --- | --- | ---: | --- | --- |
| OpenStreetMap / Overpass | `data/raw/overpass_taipei_sample.json` | 2,388 elements | legacy snapshot | Taipei-area cafe POIs; 0/2,388 have element timestamps or versions. The current `out meta` query affects future refreshes only. |
| OpenStreetMap / Overpass normalized | `data/processed/osm_cafes.normalized.jsonl` | 2,388 records | normalized | Useful for names, coordinates, addresses, websites, phones, and opening hours where OSM has tags. |
| Google Places | `scripts/collectors/collect_google_places.py` | 0 live records | policy-blocked | Dry-run only. Full-content persistence is excluded from the production dependency set. |

## Manual And Semi-Automated Sources

| Source | File | Count | Status | Notes |
| --- | --- | ---: | --- | --- |
| Manual cafe seed | `data/raw/manual_cafe_seed.csv` | 8 records | normalized | Public Dcard/PTT-style source links with confidence notes. |
| Curated seed | `data/curated/cafes.seed.jsonl` | 8 records | quarantined | Structurally valid candidates; publication audit reports 0 publishable as of 2026-08-09. |
| Search/source queue | `data/processed/source_review_queue.csv` | 11 rows | generated | Manual review queue for blogs, Dcard, PTT, Instagram, and Threads discovery. |

## Deliberately Not Automated

- Instagram public pages/posts: manual URL capture only.
- Threads public posts: manual URL capture only.
- CAPTCHA-protected or login-gated pages: blocked.
- Paywalled/private sources: blocked.
- Unofficial social scraping APIs: blocked.

## Product Readiness Notes

- OSM records are not product-ready work-friendly claims by themselves.
- OSM edit metadata is lineage only, not evidence of current operation or work
  conditions. The committed snapshot does not contain that metadata.
- Manual seed records are useful examples but need current verification before production display.
- Branch-level verification is required for chains and ambiguous cafe names.
- Retrieval dates are provenance only. All legacy `last_verified_at` values are
  now empty because no real verification was captured.
- Product work must expose field evidence and freshness and must suppress every
  unsupported, stale, conflicted, closed, or branch-ambiguous claim.
