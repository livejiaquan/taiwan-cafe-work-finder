# 2026-08-09 Product And Data Landscape Research

## 1. Research Question

What product mission and data strategy can make Taiwan Cafe Work Finder useful,
trustworthy, differentiated, maintainable, and legally deployable, given the
current repository and the market as of 2026-08-09?

## 2. Scope And Context

The review covered the complete repository, its 8 curated records, 2,388 OSM
records, pipeline and tests; current Taiwan work-cafe products; government open
data; OSM and Google policies; a remote-work certification program; and recent
user reports about working from cafes. Primary sources were preferred for data,
technical, policy, and licensing claims. Product marketing and community posts
were treated as evidence of positioning or needs, not objective truth.

## 3. Key Findings

1. The repository is a reproducible discovery/data prototype, not a public
   product. The initial assumption is correct on maturity.
2. Data reliability is a more urgent user risk than missing UI. The pipeline
   currently conflates retrieval with verification and can make old snapshots
   look newly verified.
3. A generic map and work-friendly filters are already served by stronger
   products. Differentiation must be tested around currentness and evidence.
4. No single source can prove a cafe is suitable for work. Identity/status and
   work conditions require different evidence.
5. Government and OSM sources can improve identity, address, status signals,
   coordinates, and lineage, but not subjective or rapidly changing work
   conditions.
6. Google Places is not compatible with the repository's current long-lived raw
   and normalized snapshot design without a policy-compliant redesign.
7. The sustainable product model remains unproven because recent observation
   and refresh work require people, partners, or a contribution workflow.

## 4. Evidence Summary

| Evidence | What it supports | Limits and product implication |
| --- | --- | --- |
| [Cafe Nomad API v1.2](https://cafenomad.tw/developers/docs/v1.2) | Nationwide/city APIs already expose Wi-Fi, seat, quiet, time-limit, outlet, station, and opening-time fields. | The API has no per-field observation timestamp; public access does not establish redistribution rights. Do not import without permission. |
| [Catcha homepage](https://catcha-cafes.com/) and [method](https://catcha-cafes.com/about/) | Catcha claims 100+ greater-Taipei independent cafes, nine work-space indicators, search filters, and in-person scouts. | Product-authored evidence; still proves that generic Taipei filters are not novel. |
| [Kozi](https://www.koziapp.co/) | Kozi positions 100 curated cafes across 12 Taipei districts around task-based discovery and says data comes from field research, stores, and feedback. | Marketing claims are not independent validation; they still raise the minimum viable UX bar. |
| [TDNA 2025 audit standard](https://dna.org.tw/friendly-mark/digital-nomad-friendly-mark-2025/) | A current Taiwan program uses annual certification, on-site checks, 100/40 Mbps Wi-Fi thresholds, work seating, lighting, outlets, and language support. | Only two listed certified venues are cafes/restaurants; certification data does not replace branch-level product evidence or grant unrestricted app ingestion. |
| [MOEA monthly restaurant business registrations](https://data.gov.tw/dataset/108355) | Monthly registration name, address, and status under Taiwan's Open Government Data License. | Registration status is not proof the public-facing branch is currently open or work-friendly. Entity matching can be difficult. |
| [Tourism Administration restaurant data](https://data.gov.tw/dataset/7779) | Status/time, coordinates, and update fields for covered tourism food venues. | It is not a complete cafe registry and cannot support outlets, quietness, or time-limit claims. |
| [TFDA food business registrations](https://data.gov.tw/dataset/8938) | Monthly business and address corroboration. | Legal/business identity is not the same as the marketed branch or current user experience. |
| [Taiwan Open Government Data License](https://data.gov.tw/license) | Allows reuse and derivative products for any purpose with explicit attribution. | Attribution is mandatory; the provider disclaims completeness and endorsement. |
| [OpenStreetMap license](https://www.openstreetmap.org/copyright) | OSM data can be copied and adapted with attribution and ODbL share-alike obligations. | Product attribution and derived-database obligations must be designed before distribution. OSM does not verify work conditions. |
| [Overpass output documentation](https://dev.overpass-api.de/overpass-doc/en/targets/formats.html) | `out meta` returns element versions and timestamps. | A last OSM edit timestamp is lineage, not proof of current business policy. |
| [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) | Defines attribution, identification, caching, and no-bulk-download requirements for public tiles. | Public OSM tile servers have no SLA and are not a production map backend guarantee. |
| [Google Places policies](https://developers.google.com/maps/documentation/places/web-service/policies) | Places content generally may not be prefetched, cached, or stored beyond stated exceptions; Place IDs are exempt. | The existing collector persists full API results and normalized content, so it must remain non-production until redesigned. |
| [Google Place ID guide](https://developers.google.com/maps/documentation/places/web-service/place-id) | Place IDs may be stored and Google recommends refreshing IDs older than 12 months. | A Place ID is an identifier, not permission to store the rest of a Place response indefinitely. |
| [Current Cafe Nomad closed listing for 5 Senses](https://cafenomad.tw/shop/2fc6d58b-d8d4-4f12-afd3-4ea5c875705c) and [second closed listing](https://ifoodie.tw/blog/53015e9ba9bbae5e51000001) | Concrete evidence that a legacy seed may be closed while the dataset presents positive conditions as freshly verified. | Neither is first-party confirmation, but agreement is enough to quarantine the record and invalidate the present freshness semantics. |
| [Recent Taiwan cafe-work discussion](https://www.reddit.com/r/taiwan/comments/1rbh6af/odd_rules_hours_etc_forcing_me_to_choose/) | Users report changing time limits, no Wi-Fi, laptop restrictions, food availability, seat moves, and outlet uncertainty. | Anecdotal community evidence; use it to form hypotheses, not population estimates. |

Repository profiling on 2026-08-09 found:

- curated: 8 records, 3 addresses, 0 coordinates, 4 unique source URLs, and 5
  records dependent on one Dcard article;
- OSM: 2,388 records, 1,161 with no city, 1,148 with no address, 59 placeholder
  names, 581 opening-hour strings, 295 inferred Wi-Fi-positive values, and zero
  known outlet/unlimited-time/quietness values;
- current tests: 4/4 pass, but adversarial checks showed the validator accepts an
  invalid date, object-valued city, boolean coordinates, and a `javascript:`
  contact URL;
- a default OSM normalization performed on 2026-08-09 rewrote a 2026-06-01 raw
  snapshot as `last_verified_at=2026-08-09`;
- the default curated merge produced 2,396 records by adding all OSM discovery
  candidates, contrary to the repository's stated curation policy.

## 5. Comparative Analysis

| Approach | User value | Reliability | Differentiation | Operational cost |
| --- | --- | --- | --- | --- |
| Generic nationwide map from OSM | High apparent coverage | Low for work conditions | Very low | Low ingestion, high hidden correction cost |
| Import Cafe Nomad or another directory | Fast coverage and familiar filters | Unknown freshness | Low | Licensing and dependency risk |
| Editorial Taipei guide | High quality for a small set | Medium to high if maintained | Medium | High human effort per record |
| Evidence-first verified slice | Clear current decision support | Highest if stale gates work | Promising but unproven | Moderate-to-high verification effort |
| Certification-only directory | Strong, standardized claims | High during certificate validity | Medium | Low product effort, very low cafe coverage |
| Coworking-first finder | Better fit for calls and guaranteed work infrastructure | Potentially high | Different market | Scope and mission pivot |

## 6. Tradeoffs

- Coverage versus truth: publishing fewer branches reduces discovery breadth but
  prevents costly false positives.
- Freshness versus maintenance: short TTLs protect users but require a viable
  review operation.
- Evidence detail versus speed: field-level provenance adds interface and data
  complexity, but it is the proposed reason to exist.
- Open data versus convenience: OSM/government sources are reusable with
  obligations; Google offers convenient place detail but restricts persistence.
- Cafe focus versus task fit: cafes suit quiet solo sessions better than calls;
  forcing every work scenario into cafe rankings would weaken user outcomes.

## 7. Recommended Approach

Build and test an evidence-first, branch-level trust slice for quiet solo work in
2-3 Taipei districts. First repair the data contract and publication gates. Then
verify 10-12 branches and build a small mobile-first list/detail product. Do not
build a national map, persist Google Places content, or publish the legacy seed
as recommendations.

## 8. Alternative Approaches

- A maintained editorial guide is the fallback if structured freshness is too
  expensive.
- A TDNA-certified-place companion can work if reuse rights and useful cafe
  coverage are established.
- A coworking and call-friendly-space finder is the pivot if user research shows
  calls are the higher-value task.
- A data-quality tool or contribution workflow can become the product if the
  public discovery layer is not differentiated.

## 9. Implementation Considerations

- Store retrieval, observation, and verification separately.
- Evaluate freshness at read/build time; do not persist a permanently "fresh"
  label.
- Keep OSM as a discovery/identity source and request metadata for lineage.
- Require field-to-source linkage and ensure evidence fields are actually
  present.
- Gate records and individual filters independently: a visible branch can still
  have unknown fields, but an unknown field cannot satisfy a positive filter.
- Make curation output a deterministic artifact with blockers, checksums, and
  tests before a frontend consumes it.
- Use only documented, attributable, redistributable sources in durable product
  data.
- Add user feedback only with a real moderation and refresh workflow; a form
  without an owner does not improve trust.

## 10. Open Questions And Unknowns

- Do local students, remote workers, or visitors value freshness enough to
  switch from existing products?
- Who performs and funds initial and recurring verification?
- What TTLs match actual change rates for each field?
- Can a first-party partnership or contributor workflow lower review cost?
- What are the explicit downstream rights for Cafe Nomad and TDNA venue data?
- Which code and data licenses should this repository use?
- Which hosting, domain, analytics, privacy, and incident owners will support a
  public launch?

