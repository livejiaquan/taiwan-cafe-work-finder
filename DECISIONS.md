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

Decision: Use Overpass as a discovery source. Keep Google Places live collection
disabled until a policy-compliant storage/display design is reviewed.

Reason: OSM is reproducible under ODbL with attribution but does not verify cafe
conditions. The former Google raw snapshot design conflicts with provider
storage/display restrictions; credentials do not remove that constraint.

## 2026-06-01: Confidence Model

Decision: Store confidence at both overall-record and field levels.

Reason: A cafe can have high confidence for coordinates from OSM but low confidence for quietness from a single old forum post.

## 2026-06-01: Curated Seed Versus Processed OSM

Decision: Keep `data/curated/cafes.seed.jsonl` to manually reviewed seed records, while storing the larger Overpass pull in `data/processed/osm_cafes.normalized.jsonl`.

Reason: OSM gives valuable coverage but does not usually prove work-friendly attributes. Treating all OSM POIs as curated would overstate confidence for the final product.

## 2026-08-09: Retrieval Is Not Verification

Decision: Keep retrieval, publication, source-update, field observation, and
record verification timestamps separate. Legacy records have empty
`last_verified_at` until a real verification is captured.

Reason: Re-running an old snapshot previously manufactured a current-looking
verification date and could mislead users.

## 2026-08-10: Structured Claims And Reviewed Source Policies

Decision: Field evidence is a normalized claim value plus observation date,
enumerated method, confidence, and a reviewed policy ID. Membership in an
`evidence_fields` list is never sufficient. Only the project-owned on-site
checklist policy has a publication method, and its current `.invalid` evidence
host is test-only.

Reason: Free-text rights or method labels and field membership could be forged
or disagree with the canonical value. A closed policy registry creates a
reviewable, fail-closed boundary without pretending production evidence
infrastructure exists.

## 2026-08-10: Safe Merge And Conflict Quarantine

Decision: Missing/empty inputs, empty results, and duplicate cafe IDs fail
without replacing outputs. JSONL writes use atomic replacement. Conflicting
secondary status signals remain structured unresolved conflicts; they do not
become a definitive closed claim.

Reason: Silent `setdefault` merging lost provenance, partial writes could damage
generated data, and secondary listings are sufficient to quarantine but not to
assert real-world closure.

## 2026-08-10: Stable Cafe ID Migration Deferred

Decision: Do not change the current stable cafe-ID hash during trust hardening.
Branch identity, collision handling, redirects, and ID-version migration require
a separate migration plan before verified production records exist.

Reason: Changing identity architecture inside publication-gate repairs would
mix migration risk with trust semantics and make generated diffs harder to
audit.

## 2026-08-10: Production Audit And Durable Writes Fail Closed

Decision: The CLI always audits in the production environment with an explicit
date. Future or chronologically inverted claims, unsupported districts,
duplicate IDs, unresolved evidence mismatches, and resolved conflicts without a
resolution contract remain blocked. Atomic writers preserve mode, flush the
file, replace atomically, and sync the parent directory where supported.

Reason: Test fixtures, timestamp truncation, partial provider responses, and
filesystem replacement alone are not sufficient evidence for a durable or
publication-ready artifact.
