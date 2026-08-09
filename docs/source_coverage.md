# Source Coverage

Generated: 2026-06-01

## Automated Sources

| Source | File | Count | Status | Notes |
| --- | --- | ---: | --- | --- |
| OpenStreetMap / Overpass | `data/raw/overpass_taipei_sample.json` | 2,388 elements | collected | Taipei-area cafe POIs collected from public Overpass API. |
| OpenStreetMap / Overpass normalized | `data/processed/osm_cafes.normalized.jsonl` | 2,388 records | normalized | Useful for names, coordinates, addresses, websites, phones, and opening hours where OSM has tags. |
| Google Places | `scripts/collectors/collect_google_places.py` | 0 live records | optional | Dry-run verified. Live collection requires `GOOGLE_MAPS_API_KEY`. |

## Manual And Semi-Automated Sources

| Source | File | Count | Status | Notes |
| --- | --- | ---: | --- | --- |
| Manual cafe seed | `data/raw/manual_cafe_seed.csv` | 8 records | normalized | Public Dcard/PTT-style source links with confidence notes. |
| Curated seed | `data/curated/cafes.seed.jsonl` | 8 records | validated | Human-review-oriented seed records with source URLs. |
| Search/source queue | `data/processed/source_review_queue.csv` | 11 rows | generated | Manual review queue for blogs, Dcard, PTT, Instagram, and Threads discovery. |

## Deliberately Not Automated

- Instagram public pages/posts: manual URL capture only.
- Threads public posts: manual URL capture only.
- CAPTCHA-protected or login-gated pages: blocked.
- Paywalled/private sources: blocked.
- Unofficial social scraping APIs: blocked.

## Product Readiness Notes

- OSM records are not product-ready work-friendly claims by themselves.
- Manual seed records are useful examples but need current verification before production display.
- Branch-level verification is required for chains and ambiguous cafe names.
- Phase 2 should expose confidence and last verified dates rather than treating all attributes as equally reliable.
