# 2026-08-11 MVP Browse/Find Readiness Decision

## 1. Research Question

Can this repository truthfully support a narrow public browse/find flow today
using only evidence that passes the production publication contract? If not,
what is the highest-value bounded step toward a useful public product?

## 2. Scope And Context

This review used commit `74d4711`, the 8-record curated seed, the explicit
2,396-record manual-plus-OSM discovery merge, the production audit as of
2026-08-11, current source policies, and current first-party product and
government pages. It did not treat OSM presence, business registration, source
retrieval, competitor data, or an old forum report as proof that a cafe is open
and suitable for work.

The intended public grain is one physical cafe branch. The core user task is to
find a currently open Greater Taipei branch for quiet solo work or study using
fresh, decision-field evidence.

## 3. Key Findings

1. **Public browse/find is a no-go.** The curated audit is 0/8 publishable and
   the explicit discovery audit is 0/2,396 publishable.
2. The curated set has 0 resolved branch identities, 0 records asserted open,
   0 coordinates, 0 verification timestamps, and 0 dated observed claims.
3. OSM supplies 2,388 coordinate-bearing discovery candidates, but 0 resolved
   branch identities, 0 verified operating records, and 0 observed work claims.
   It cannot become apparent product coverage.
4. No executable source policy currently permits production publication. The
   only positive-path project observation policy uses a `.invalid` host and is
   test-only.
5. No whitelist public projection exists. Canonical records and audit output
   contain internal fields and are explicitly forbidden as client data.
6. Existing products already provide broad lists, maps, and work filters. A
   small unverified UI would be both less useful and less trustworthy.
7. Government open data can corroborate registered identity/address/status at
   business level, but it cannot prove a marketed branch is open today or has
   outlets, Wi-Fi, quietness, or no time limit.

## 4. Evidence Summary

### Repository quality profile

| Check | Curated | Manual + OSM discovery | Product implication |
| --- | ---: | ---: | --- |
| Total records | 8 | 2,396 | Candidate count is not coverage. |
| Publishable | 0 | 0 | No cafe result may be shown. |
| Resolved branches | 0 | 0 | No branch-level unit of truth exists. |
| `operational_status=open` | 0 | 0 | No current open claim exists. |
| Coordinates | 0 | 2,388 | OSM location does not transfer trust to work conditions. |
| Record verification timestamps | 0 | 0 | Nothing has completed real verification. |
| Dated observed claims | 0 | 0 | No decision field has an observation date. |
| Publishable districts | 0 | 0 | A district filter would be empty. |

The production `--require-publishable` command exited 3, as designed. The most
frequent curated blockers were `evidence_unknown` (124),
`evidence_unsupported` (16), `required_value_missing` (13), and eight each for
unresolved branch, unusable operating status, out-of-scope claim, missing
geofence evidence, and missing record verification. The one conflicted record
remains quarantined.

Reproducible artifacts were written to
`/tmp/taiwan-cafe-mvp-readiness.zt6dnC` for this run. Their SHA-256 values match
the prior Trust Foundation handoff:

- curated audit: `94a9a4cfcbe7418c9587b127b83df7e2ee87e13b7f3a3f6f5b35849ab125e2c0`
- discovery: `b67f76ebc8f32973e4000a312bd8bb088f70faf94b38715b647f63b4dbbdef62`
- discovery audit: `080b3b19f83bc184f2bea97480c0094d452f0cbad9abe10ac23a94f0c81d8ab6`

### Current external evidence

| Source | Current evidence | Safe use and limitation |
| --- | --- | --- |
| [Cafe Nomad developer/API pages](https://cafenomad.tw/developers) | Public list/map coverage and work/custom filters; API fields include Wi-Fi, quietness, time-limit, outlets, address, and coordinates. | Confirms generic browse/filter is already served. The documented fields do not include per-field observation timestamps, and public API access alone does not establish downstream redistribution rights. |
| [Catcha homepage](https://catcha-cafes.com/) and [example branch](https://catcha-cafes.com/place/come-true-coffee/) | Claims 100+ Greater Taipei cafes, nine workspace indicators, condition search, branch address/hours, and work attributes; the example page shows an author update date. | Confirms a high existing UX/content bar. Product-authored values are competitor evidence, not reusable project truth, and one page update date is not field-level freshness. |
| [MOEA restaurant registrations](https://data.gov.tw/dataset/108355) | Monthly business name, address, and registration status under the Taiwan Open Government Data License. | Useful identity/status corroboration only. Registration is not proof that a public-facing branch is open today or work-friendly. |
| [MOEA beverage-shop registrations](https://data.gov.tw/dataset/32685) | Monthly F501030 registrations with business name, address, status, and open-data licensing. | Helps candidate/entity review, but legal registration and marketed cafe branch identity may differ. |
| [TFDA food-business registrations](https://data.gov.tw/dataset/8938) | Business name, unified number, address, food registration number, and monthly open-data files/API. | Can corroborate a regulated operator; cannot support current work-condition claims. |
| [OpenStreetMap license](https://www.openstreetmap.org/copyright) | ODbL reuse requires OpenStreetMap/contributor credit and share-alike treatment for derived databases. | Discovery/location only here; attribution and database-distribution obligations still require a deliberate public design. |
| [Google Places policy](https://developers.google.com/maps/documentation/places/web-service/policies) | Places content generally cannot be prefetched, cached, or stored beyond exceptions; Place IDs are exempt; display/attribution rules apply. | Confirms the disabled full-response persistence path must stay disabled. A key is not permission to build a durable cafe dataset. |

## 5. Comparative Analysis

| Option now | Truthfulness | Immediate user value | Differentiation | Decision |
| --- | --- | --- | --- | --- |
| Publish legacy 8 | Critical failure | Misleading | Low | Reject. |
| Publish OSM 2,388 | Critical failure | Apparent breadth only | Very low | Reject. |
| Build an empty browse/filter shell | Honest if empty, but implies a product with no results | Near zero | None | Do not build now. |
| Import a competitor/API dataset | Rights and freshness unresolved | Fast apparent value | Low | Reject without permission and field-level freshness. |
| Private 3-branch verification-operations pilot | Honest and measurable | No public value yet | Tests the evidence-first wedge | Proceed next. |
| Public 10–12 branch verified slice | Truthful only after all gates pass | Useful narrow choice | Potentially meaningful | Conditional next milestone. |

## 6. Tradeoffs

- Delaying UI preserves trust but postpones user-visible learning.
- A three-branch private pilot is too small for public browse/find, but it is the
  cheapest way to test verification cost and the evidence model with reality.
- Government and OSM enrichment reduce identity work while adding entity-match,
  attribution, and licensing responsibilities; they do not eliminate visits.
- Short freshness windows reduce stale recommendations but create a recurring
  human operations cost that is still unmeasured.

## 7. Recommended Approach

Do not implement a public MVP vertical slice in this iteration. Run a private
verification-operations preflight on exactly three real branches in one
district before scaling data collection:

1. approve a real project-controlled evidence host and production source policy;
2. define reviewer identity, checklist, consent/notice, retention, correction,
   and conflict-resolution rules;
3. corroborate branch identity/current operation separately from on-site work
   conditions;
4. record time spent per branch and every decision-field observation;
5. require 3/3 records to pass the production audit without exemptions;
6. expand to 10–12 branches across 2–3 districts only if the measured initial
   and refresh cost keeps roadmap hypothesis H2 plausible.

The public browse/find go gate remains at least 10 publishable branches across
2–3 districts plus a leak-tested whitelist projection. Any blocked, unknown,
stale, conflicted, or internal-only record reaching the client is a stop event.

## 8. Alternative Approaches

- If 3/3 branches cannot pass sustainably, pivot to a one-district maintained
  editorial guide with explicit verification dates.
- If work-condition maintenance is not viable, ship no cafe directory and
  consider a verification/contribution workflow as the product.
- If a public URL is required before coverage exists, publish only a static
  methodology/status page saying there are no verified recommendations yet.
  It must contain no cafe names, filters, OSM/forum candidates, or internal
  audit metadata.

## 9. Implementation Considerations

- This iteration intentionally adds no frontend, sample feed, production policy,
  or fake evidence host.
- The next implementation must not declare a production policy until the real
  host, governance, reviewer ownership, and rights basis exist.
- The future public projection must be a whitelist derived only from records
  whose production audit decision is `publishable=true`; it needs leak tests
  before any UI consumes it.
- Field operations must measure initial and refresh minutes instead of assuming
  the roadmap maintenance target is feasible.
- Browser/mobile/accessibility/build validation becomes mandatory only when a
  real public flow exists. It is not meaningful for this no-go decision.

Reproduce the two coverage decisions without changing repository artifacts:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 \
  scripts/quality/audit_publication_readiness.py \
  --input data/curated/cafes.seed.jsonl \
  --as-of 2026-08-11 \
  --output /tmp/cafe-curated-audit.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 \
  scripts/normalize/merge_curated.py \
  --inputs data/processed/manual_cafes.normalized.jsonl \
           data/processed/osm_cafes.normalized.jsonl \
  --output /tmp/cafe-discovery.jsonl

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 \
  scripts/quality/audit_publication_readiness.py \
  --input /tmp/cafe-discovery.jsonl \
  --as-of 2026-08-11 \
  --output /tmp/cafe-discovery-audit.json
```

## 10. Open Questions And Unknowns

- Who owns field verification and monthly refresh work?
- What real host/domain stores evidence, and who can correct or remove it?
- What notice or consent is needed for observational notes or submitted media?
- Which three branches and district minimize travel while remaining
  representative of the intended user task?
- Do provisional 30/90-day freshness windows match real change rates?
- Which repository code/data license and OSM derived-database strategy will be
  approved before public distribution?
