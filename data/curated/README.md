# Curated Data

This folder stores human-review-ready or product-seed datasets.

Primary Phase 1 output:

- `cafes.seed.jsonl`

Every curated cafe record must include at least one source URL and source-level
provenance metadata. `last_verified_at` stays empty until a real verification
occurs; a retrieval date must never fill it.

The default merge includes reviewed manual candidates only. Structural presence
in this folder does not mean publication-ready. Run
`scripts/quality/audit_publication_readiness.py --as-of YYYY-MM-DD` before any
product use; the date is intentionally required for reproducibility. See
`docs/data-publication-contract.md`.
