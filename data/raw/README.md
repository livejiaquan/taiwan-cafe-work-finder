# Raw Data

This folder stores source snapshots and manually reviewed source seeds.

Raw files should preserve source-specific shape whenever practical. Do not hand-edit API snapshots except to remove secrets before committing or sharing.

Current files:

- `manual_cafe_seed.csv`: manually curated seed records from public forum/article sources.
- `manual_cafe_seed.template.csv`: exact current input header for new review rows;
  copy the header, never use invented sample values as evidence.
- `cafe_conflicts.json`: reproducible unresolved conflict signals that quarantine
  a matched candidate without converting secondary reports into fact.
- `source_seed_queries.csv`: search terms for manual source discovery.
- `overpass_taipei_query.overpassql`: reproducible Overpass query for Taipei cafe POIs.

Current manual review columns include `observed_at`, enumerated
`verification_method`, reviewed `policy_id`, `verified_at`,
`branch_identity_status`, `operational_status`, and exact rights metadata. The
legacy seed predates those columns and is accepted only as quarantined forum
input. Use the template for new rows and leave values empty rather than infer
them.

The current Overpass collector/query uses `out meta` so future snapshots can
retain element edit timestamps and versions as source metadata. The committed
legacy snapshot predates that query and has neither field for any of its 2,388
elements. Edit metadata, when present, is source lineage rather than a field
observation. Live collection rejects empty results, error/partial-result
remarks, and incomplete or non-cafe elements before touching the raw snapshot;
a successful snapshot is written atomically.
