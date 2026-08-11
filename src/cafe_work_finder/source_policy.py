from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


VERIFICATION_METHODS = {
    "source_report",
    "dataset_snapshot",
    "provider_api",
    "on_site_checklist",
}

SOURCE_POLICIES: dict[str, dict[str, Any]] = {
    "legacy_forum_v1": {
        "source_types": {"forum"},
        "rights_statuses": {"unknown"},
        "claim_methods": {"source_report"},
        "publication_methods": set(),
        "publication_environments": set(),
        "rights_basis": "",
        "attribution": "",
        "url_prefixes": ("https://www.dcard.tw/", "https://www.ptt.cc/"),
        "purpose": "Legacy forum discovery and quarantine only.",
    },
    "osm_odbl_discovery_v1": {
        "source_types": {"openstreetmap"},
        "rights_statuses": {"attribution_required"},
        "claim_methods": {"dataset_snapshot"},
        "publication_methods": set(),
        "publication_environments": set(),
        "rights_basis": "Open Database License (ODbL) 1.0",
        "attribution": "© OpenStreetMap contributors",
        "url_prefixes": ("https://www.openstreetmap.org/",),
        "purpose": "ODbL place discovery with attribution; never real-world verification.",
    },
    "google_places_restricted_v1": {
        "source_types": {"google_places"},
        "rights_statuses": {"restricted"},
        "claim_methods": {"provider_api"},
        "publication_methods": set(),
        "publication_environments": set(),
        "rights_basis": "Google Maps Platform Terms",
        "attribution": "Google Maps",
        "url_prefixes": (
            "https://maps.google.com/",
            "https://www.google.com/",
            "https://google.com/",
        ),
        "purpose": "Policy-restricted non-production reference path.",
    },
    "project_field_observation_v1": {
        "source_types": {"field_observation"},
        "rights_statuses": {"cleared"},
        "claim_methods": {"on_site_checklist"},
        "publication_methods": {"on_site_checklist"},
        "publication_environments": {"test"},
        "rights_basis": "Project-owned on-site observation",
        "attribution": "Taiwan Cafe Work Finder field observation",
        "url_prefixes": (
            "https://evidence.taiwan-cafe-work-finder.invalid/observations/",
        ),
        "purpose": "Project-owned, reviewed on-site checklist observations.",
    },
}


def validate_source_policy(source: dict[str, Any], index: int) -> None:
    policy_id = source["policy_id"]
    policy = SOURCE_POLICIES.get(policy_id)
    if policy is None:
        raise ValueError(f"source_links[{index}].policy_id is not reviewed: {policy_id!r}")
    if source["source_type"] not in policy["source_types"]:
        raise ValueError(
            f"source_links[{index}].source_type {source['source_type']!r} is not allowed by {policy_id}"
        )
    if source["rights_status"] not in policy["rights_statuses"]:
        raise ValueError(
            f"source_links[{index}].rights_status {source['rights_status']!r} is not allowed by {policy_id}"
        )
    if source["rights_basis"] != policy["rights_basis"]:
        raise ValueError(f"source_links[{index}].rights_basis does not match reviewed policy {policy_id}")
    if source["attribution"] != policy["attribution"]:
        raise ValueError(f"source_links[{index}].attribution does not match reviewed policy {policy_id}")
    if not any(source["url"].startswith(prefix) for prefix in policy["url_prefixes"]):
        host = urlparse(source["url"]).hostname or ""
        raise ValueError(
            f"source_links[{index}].url host/prefix {host!r} is not allowed by reviewed policy {policy_id}"
        )
    for claim_index, claim in enumerate(source["claims"]):
        method = claim["verification_method"]
        if method not in policy["claim_methods"]:
            raise ValueError(
                f"source_links[{index}].claims[{claim_index}].verification_method "
                f"{method!r} is not allowed by {policy_id}"
            )


def publication_claim_allowed(
    source: dict[str, Any],
    claim: dict[str, Any],
    environment: str,
) -> bool:
    policy = SOURCE_POLICIES[source["policy_id"]]
    return (
        environment in policy["publication_environments"]
        and claim["verification_method"] in policy["publication_methods"]
    )
