# Product Mission And Evidence-Based Roadmap

Last reviewed: 2026-08-11 (Asia/Taipei)

## Mission

Help a person in greater Taipei choose a cafe for a quiet solo work or study
session **today**, without wasting a trip. Every decision-critical claim must say
what supports it, when it was observed, and whether it is still fresh. Unknown,
stale, conflicted, or branch-ambiguous information must never be presented as a
positive recommendation.

The first audience is a local person carrying a laptop who needs a place for a
focused individual session. Online calls are deliberately excluded until the
product has direct evidence for network quality, background noise, and call
policy. A cafe is not automatically an appropriate meeting space.

## Why This Mission Changed

The original direction was a Taiwan-wide work-friendly cafe finder with map and
filters. Current evidence changes the priority:

- The repository is still a Phase 1 data foundation. It has no product UI,
  backend service, deployment, analytics, SEO, or domain configuration.
- The eight curated records are not safe production truth: only three have an
  address, none has coordinates, five share one Dcard source, and every record
  labels a source retrieval date as `last_verified_at`.
- One record, 5 Senses Cafe, still makes positive work-condition claims even
  though its only source describes visits in 2013-2015 and two current listings
  mark the same branch closed. This is a concrete false-freshness failure, not a
  theoretical concern.
- The 2,388 OSM records provide discovery coverage, but no records have evidence
  for outlets, unlimited time, or quietness. They cannot be promoted into a
  work-friendly directory.
- Cafe Nomad, Catcha, and Kozi already provide broad discovery, work filters, or
  curated cafe experiences. A generic map/list would be a weaker duplicate.

The differentiated product bet is therefore **decision reliability**, not
record count: field-level provenance, visible freshness, conflict handling, and
automatic suppression of unsupported claims.

## Product Principles

1. Retrieval is not verification. `retrieved_at`, `observed_at`, and
   `verified_at` have different meanings.
2. Place identity confidence does not transfer to work-condition confidence.
   Government or OSM data can support identity and location without proving
   outlets, Wi-Fi, quietness, or time limits.
3. A branch is the unit of truth. Chain-level rules are never applied to an
   unidentified branch.
4. Freshness is enforced, not decorative. Stale claims are removed from
   positive filtering and ranking.
5. Unknown is an honest product state. Empty, stale-only, conflict, loading, and
   error states must remain useful and understandable.
6. A small verified slice is more valuable than national-looking coverage with
   hidden uncertainty.

## Publication Contract

A branch may appear as a positive recommendation only when all of the following
are true:

- its identity resolves to one physical branch;
- name, address, and coordinates are present;
- current operating status has recent supporting evidence;
- every displayed positive work condition points to evidence that explicitly
  supports that field;
- evidence includes source URL, source type, `retrieved_at`, `observed_at`,
  verification method, and an expiry or applicable freshness policy;
- no unresolved closure, branch, or policy conflict exists;
- source licensing and attribution requirements are known and implemented.

Provisional freshness windows for the first field study are 30 days for
operating status, opening hours, Wi-Fi, time limits, and quietness; and 90 days
for outlet availability. These are hypotheses to test, not universal facts.

`candidate`, `stale`, `conflicted`, `closed`, and `rejected` records remain
available to the curation workflow but do not enter positive search results.

## Falsifiable Product Hypotheses

### H1 - Trust changes the decision

At least 6 of 8 target users can find a suitable branch within 90 seconds and
cite evidence or freshness as a reason for choosing it.

### H2 - The data operation is sustainable

Across 2-3 Taipei districts, at least 12 branch-resolved cafes can be initially
verified in a median of 15 minutes each and refreshed in a median of 5 minutes
each per month. At least 80% of decision-critical fields have unexpired
evidence.

### H3 - Recommendations survive reality

At least 8 of the first 10 independent visits confirm the three conditions that
drove the selection. There must be zero closed-cafe recommendations and zero
high-harm errors such as no outlet after an outlet-positive filter or an
undisclosed time limit after an unlimited-time filter.

### H4 - The wedge is differentiated

In an equivalent task against Cafe Nomad and Catcha, at least 5 of 8 users prefer
this product specifically because the result is current and evidence is clear,
not only because of visual styling.

### H5 - Stale suppression is complete

Automated tests show that 100% of expired, unsupported, conflicted, closed, or
branch-ambiguous claims are excluded from positive filters and ranking.

## Roadmap

### Iteration 1 - Trust Foundation (complete at `74d4711`)

Outcome: the pipeline can no longer manufacture freshness or accidentally
publish discovery candidates.

Acceptance criteria:

- preserve the recovered Phase 1 state in a local Git baseline and work on a
  feature branch;
- separate source retrieval from real-world observation/verification;
- derive OSM retrieval time from the raw snapshot, not the normalization run;
- collect OSM element metadata for future refreshes;
- make evidence fields reflect fields actually present;
- make the default curated merge exclude OSM discovery records;
- strengthen structural validation for dates, sources, URLs, coordinates, and
  field types;
- add a deterministic publication-readiness audit and regression tests;
- quarantine every legacy seed from positive publication until it is
  reverified;
- document Google Places persistence restrictions and keep that path out of the
  first production dependency set.

This iteration is successful only if the existing seed is correctly reported as
not publishable. A green test suite alone is insufficient.

### Iteration 2 - Verified Trust Slice

Outcome: 10-12 genuinely usable branches across 2-3 Taipei districts.

Before collecting the full slice, run a private three-branch verification-
operations preflight in one district. It is not a public directory and must not
feed a UI. Proceed only after a real project-controlled evidence host and
production policy exist, all three records pass without exemptions, and actual
initial/refresh time keeps H2 plausible. See
`docs/research/2026-08-11-mvp-browse-find-readiness.md`.

Acceptance criteria:

- all branches meet the publication contract;
- current official or authoritative sources support identity and operating
  status;
- dated direct observation or recent independent reports support positive work
  conditions;
- source and maintenance time are logged;
- no Cafe Nomad, Catcha, Google Places, or other third-party dataset is imported
  without explicit downstream rights.
- a whitelist public projection passes leak tests before any client consumes it.

### Iteration 3 - Thin Public Product

Outcome: a stranger can complete the core selection task on a phone.

Initial scope:

- Traditional Chinese, mobile-first list and detail flow;
- district, intended stay length, outlet, and quiet solo-work filters;
- visible freshness on every result and field-level evidence on detail;
- honest loading, empty, error, stale-only, and conflict states;
- keyboard and screen-reader basics, representative mobile/desktop rendering,
  clean console, production build, metadata, robots/sitemap, and custom-domain
  configuration;
- no complex map until it demonstrably improves the core task.

### Iteration 4 - Outcome And Operations Validation

Outcome: prove that the product is useful and maintainable.

- run the eight-person comparative task study;
- independently verify at least ten visits;
- measure verification and refresh effort;
- implement feedback triage, stale reports, scheduled refreshes, and audit logs;
- deploy only after licensing, privacy, domain, and attribution decisions are
  explicit.

## Continue, Stop, And Pivot Gates

Continue private verification when the publication contract is testable and a
three-branch pilot passes without exemptions at a plausible maintenance cost.
Continue to public browse/find only when at least ten branches across 2-3
districts meet the trust bar, a whitelist projection passes leak tests,
freshness affects user decisions, and maintenance cost is viable.

Stop public launch when any legacy seed is recommended without re-verification,
when stale/unknown claims pass positive filters, when data rights are unclear,
or when only UI/build work is complete.

Pivot to a smaller editorial guide or one district when twelve branches cannot
be maintained. Remove the provenance-first positioning if users do not value it.
Route online-call needs to coworking spaces if cafes consistently fail that
task. Stop building a generic directory if direct comparison shows no meaningful
preference.

## Known Decision Blockers

- No on-site verification capability or durable reviewer network exists yet.
- The repository has no license; code/data licensing must be decided before
  public distribution.
- Cafe Nomad exposes an API but its downstream redistribution license is not
  explicit.
- Google Places content cannot be persisted using the current raw/normalized
  snapshot design.
- Hosting account, production domain, analytics, privacy owner, and feedback
  operations are not configured.

These blockers do not prevent Iteration 1. They do prevent claiming a launchable
public directory.
