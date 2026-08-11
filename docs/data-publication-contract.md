# Data And Publication Contract

Last updated: 2026-08-10

The canonical JSONL dataset is a curation workspace, not automatically a public
recommendation feed. Structural validity and publication readiness are separate
checks. A structurally valid `candidate` can contain honest unknowns; only the
publication audit may promote a record.

The JSON Schema is structural interchange documentation only. It is not
publication authority. The Python validator, reviewed source-policy registry,
and production publication audit are all mandatory.

## Time Semantics

- `source_links[].retrieved_at`: when this project downloaded or opened a
  source. It proves provenance only.
- `source_links[].published_at`: when a publisher posted the source. It does not
  prove when a cafe condition was observed.
- `source_links[].source_updated_at`: a source-system edit timestamp, such as
  OSM element metadata. It is not an observation.
- `source_links[].claims[].observed_at`: when that specific field value was
  actually observed.
- `last_verified_at`: the latest completed record-level verification. It stays
  empty when no such verification exists.

Normalizers must never fill `observed_at` or `last_verified_at` from retrieval,
publication, normalization-run, or OSM edit timestamps.

Supporting chronology is monotonic:
`published_at/source_updated_at <= retrieved_at <= last_verified_at <= as-of`,
and each claim must satisfy `observed_at <= retrieved_at`. Future claims are
globally blocked even if another matching claim is fresh. Datetimes must carry
an explicit timezone offset. The audit compares full instants; same-day mixed
date/datetime precision is not enough to prove chronology and fails closed.

## Branch And Operating State

`branch_identity_status` is `resolved`, `ambiguous`, or `unknown`. An independent
cafe can be resolved with a unique full address and coordinates; a nonempty
`branch_name` is not required. A chain candidate that still says "branch needs
verification" remains `unknown` or `ambiguous`.

`operational_status` is `open`, `temporarily_closed`, `closed`, `conflicted`, or
`unknown`. Publication requires `open` plus explicit, observed evidence no more
than 30 days old. Retrieval of a live page is not by itself operating-status
verification.

## Field Evidence

Every source contains structured `claims`. Each claim binds a canonical field
path to its normalized value, observation date, enumerated verification method,
and confidence. `evidence_fields` must exactly equal that source's claim fields;
it is a compatibility index, not evidence by itself. Publication compares fresh
claim values to the canonical value and fails closed on a fresh mismatch.
Every claim-bearing field is audited, including contact and branch-name claims;
the gate does not ignore mismatches merely because a field is not a positive
filter.

Publication additionally requires:

- a dated claim-level `observed_at` and policy-approved verification method;
- source and field confidence of `high` or `medium`;
- usable rights metadata;
- an unexpired observation under the field policy;
- no unresolved record conflict.

The initial policies are 30 days for operating status, opening hours, Wi-Fi,
time limits, and quietness; 90 days for outlets; and 365 days for identity and
location. These are product hypotheses and must be revised from field evidence.

Every non-`unknown` or nonempty work attribute, including negative and limiting
values such as `no`, `none`, `limited`, and `lively`, is audited and must have a
fresh matching claim. `unlimited_time=conditional` is blocked until the actual
condition can be represented. Online-meeting suitability is out of the first
product scope and must remain `unknown` in a publishable record.

Publication also requires fresh matching claims for branch identity, city, and
district. City must resolve to Taipei or New Taipei and coordinates must fall
inside the deliberately broad Greater Taipei sanity geofence: latitude
24.65-25.35 and longitude 121.25-122.10. This is not a neighborhood boundary;
it catches obvious out-of-scope coordinates such as Tokyo. Both checks and the
exact scope are emitted in every audit report.

Taipei and New Taipei each use an explicit district allowlist; generic values
such as `Multiple` are outside publication scope. The taxonomy is checked
against the official [Taipei administrative districts](https://www.gov.taipei/cp.aspx?n=1F076481DD9E556B)
and [New Taipei district-office directory](https://www.ntpc.gov.tw/ch/home.jsp?id=f290df80d79e8c18).

## Rights And Attribution

Each source records a reviewed `policy_id`, `rights_status`, `rights_basis`, and
`attribution`. See `docs/source-policy-registry.md`; policy metadata is exact and
cannot be replaced by free text.

- `cleared` requires a nonempty basis explaining the permission or ownership.
- `attribution_required` requires both a rights basis and the attribution text.
- `restricted` and `unknown` sources cannot support public claims.

OSM candidates carry ODbL and OpenStreetMap attribution metadata. Google Places
content is marked `restricted`; full response snapshots and normalized content
remain a non-production research path and are excluded from the default merge.
Only permitted identifiers or a policy-compliant runtime integration may be
considered later.

Production audit is fixed to `environment=production`; the current `.invalid`
project observation policy has no production permission. `environment=test`
exists only for unit fixtures and is recorded in the audit result. Resolved
conflicts also remain production-blocked until reviewer identity, resolution
source, date, and method are modeled and validated.

## Public Versus Internal Fields

Only fields explicitly passed by the production publication audit may become UI
content. Nonempty `branch_name` and every `contact.*` value require fresh
matching claims. `aliases`, `external_ids`, record `notes`, source metadata,
claims, confidence internals, and conflict-workflow metadata are internal-only;
the UI must never render them directly. A future UI contract must explicitly
select and safely label public fields.

The audit report is a diagnostic decision artifact, not a public data feed. A
future UI pipeline must build a separate whitelist-based publication projection
containing only records with `publishable=true` and only explicitly approved
display fields. It must never serialize canonical records, audit blockers,
source metadata, or internal workflow fields directly to clients.

## Commands

Regenerate reviewed candidates and the safe default curated file:

```bash
PYTHONPATH=src python scripts/normalize/normalize_manual.py
PYTHONPATH=src python scripts/normalize/merge_curated.py
```

OSM is an explicit discovery-only input:

```bash
PYTHONPATH=src python scripts/normalize/merge_curated.py \
  --inputs data/processed/manual_cafes.normalized.jsonl \
           data/processed/osm_cafes.normalized.jsonl \
  --output /tmp/cafe-discovery-candidates.jsonl
```

Run a reproducible publication audit:

```bash
PYTHONPATH=src python scripts/quality/audit_publication_readiness.py \
  --as-of 2026-08-09 \
  --output /tmp/cafe-publication-audit.json
```

The legacy eight-record seed is expected to report `0 publishable`. That is a
successful quarantine result, not a launch-ready dataset.

Atomic writers flush the file, replace the target, then sync its parent
directory where supported. If a non-portability directory-sync error occurs
after replacement, the CLI reports `target replaced; directory durability
uncertain`; it does not incorrectly promise that the old target was preserved.
