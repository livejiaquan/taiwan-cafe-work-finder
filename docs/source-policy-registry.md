# Reviewed Source Policy Registry

Last updated: 2026-08-10

The executable registry is `src/cafe_work_finder/source_policy.py`. A source is
structurally invalid unless its policy ID, source type, rights status, exact
rights basis, exact attribution, URL prefix, and every claim verification
method match one reviewed entry. Free-text claims such as "assumed reusable"
never grant publication rights.

| Policy ID | Source and URL | Method | Rights | Publication use |
| --- | --- | --- | --- | --- |
| `legacy_forum_v1` | Public `www.dcard.tw` or `www.ptt.cc` forum URL | `source_report` | `unknown`; empty basis/attribution | Never; discovery and quarantine only |
| `osm_odbl_discovery_v1` | `www.openstreetmap.org` | `dataset_snapshot` | ODbL 1.0; `© OpenStreetMap contributors` | Never; place discovery only |
| `google_places_restricted_v1` | Reviewed Google Maps URL prefixes | `provider_api` | Google Maps Platform Terms | Never; restricted non-production reference |
| `project_field_observation_v1` | `evidence.taiwan-cafe-work-finder.invalid/observations/` | `on_site_checklist` | Exact project-owned observation basis and attribution | Unit-test environment only; never production |

The `.invalid` project evidence host is deliberately test-only and can never
resolve on the public Internet. It proves the gate has a positive path without
pretending a production evidence service exists. Before real records can
publish, a controlled evidence host and ownership/reviewer policy must receive a
new reviewed registry entry.
