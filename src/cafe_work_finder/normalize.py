from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from .schema import (
    BRANCH_IDENTITY_VALUES,
    CONFIDENCE_VALUES,
    OPERATIONAL_STATUS_VALUES,
    RIGHTS_STATUS_VALUES,
    WORK_ATTRIBUTE_ENUMS,
    is_http_url,
    is_iso_date_or_datetime,
)


MANUAL_COLUMNS = [
    "name",
    "branch_name",
    "city",
    "district",
    "address",
    "lat",
    "lng",
    "unlimited_time",
    "outlets",
    "wifi",
    "quietness",
    "seat_comfort",
    "meeting_suitability",
    "solo_work_suitability",
    "study_suitability",
    "online_meeting_suitability",
    "long_stay_suitability",
    "opening_hours",
    "minimum_order",
    "price_level",
    "food_available",
    "reservation",
    "website_url",
    "instagram_url",
    "facebook_url",
    "threads_url",
    "google_maps_url",
    "phone",
    "source_url",
    "source_title",
    "source_type",
    "published_at",
    "retrieved_at",
    "observed_at",
    "verification_method",
    "policy_id",
    "verified_at",
    "branch_identity_status",
    "operational_status",
    "rights_status",
    "rights_basis",
    "attribution",
    "confidence",
    "confidence_notes",
    "notes",
]


def normalize_space(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable_cafe_id(
    name: str,
    city: str,
    district: str,
    address: str,
    prefix: str = "manual",
) -> str:
    key = "|".join(
        normalize_space(part).casefold()
        for part in [name, city, district, address]
    )
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def parse_float(value: object) -> float | None:
    text = normalize_space(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def enum_or_unknown(field: str, value: object) -> str:
    text = normalize_space(value).casefold()
    allowed = WORK_ATTRIBUTE_ENUMS[field]
    return text if text in allowed else "unknown"


def coordinates_from_values(lat_value: object, lng_value: object) -> dict[str, float] | None:
    lat = parse_float(lat_value)
    lng = parse_float(lng_value)
    if lat is None or lng is None:
        return None
    return {"lat": lat, "lng": lng}


def contact_from_row(row: dict[str, Any]) -> dict[str, str]:
    fields = [
        "website_url",
        "instagram_url",
        "facebook_url",
        "threads_url",
        "google_maps_url",
        "phone",
    ]
    return {field: normalize_space(row.get(field)) for field in fields if normalize_space(row.get(field))}


def normalized_choice(value: object, allowed: set[str], default: str) -> str:
    normalized = normalize_space(value).casefold()
    return normalized if normalized in allowed else default


def make_claim(
    field: str,
    value: object,
    observed_at: str,
    verification_method: str,
    confidence: str,
) -> dict[str, Any]:
    return {
        "field": field,
        "value": value,
        "observed_at": observed_at,
        "verification_method": verification_method,
        "confidence": confidence,
    }


def source_policy_for_type(source_type: str) -> tuple[str, str, str]:
    policies = {
        "forum": ("legacy_forum_v1", "source_report", "unknown"),
        "field_observation": ("project_field_observation_v1", "on_site_checklist", "cleared"),
    }
    return policies.get(source_type, ("legacy_forum_v1", "source_report", "unknown"))


def manual_claims(
    row: dict[str, Any],
    work_attributes: dict[str, str],
    contact: dict[str, str],
    branch_identity_status: str,
    operational_status: str,
) -> list[dict[str, Any]]:
    confidence = normalized_choice(row.get("confidence"), CONFIDENCE_VALUES, "unknown")
    observed_at = normalize_space(row.get("observed_at"))
    source_type = normalize_space(row.get("source_type")) or "manual"
    _, default_method, _ = source_policy_for_type(source_type)
    method = normalize_space(row.get("verification_method")) or default_method
    values: list[tuple[str, object]] = []
    for field, value in [
        ("canonical_name", normalize_space(row.get("name"))),
        ("branch_name", normalize_space(row.get("branch_name"))),
        ("city", normalize_space(row.get("city"))),
        ("district", normalize_space(row.get("district"))),
        ("address", normalize_space(row.get("address"))),
        ("coordinates", coordinates_from_values(row.get("lat"), row.get("lng"))),
    ]:
        if value is not None and (not isinstance(value, str) or value):
            values.append((field, value))
    if branch_identity_status != "unknown":
        values.append(("branch_identity_status", branch_identity_status))
    if operational_status != "unknown":
        values.append(("operational_status", operational_status))
    for field, value in work_attributes.items():
        if field in WORK_ATTRIBUTE_ENUMS:
            if value != "unknown":
                values.append((f"work_attributes.{field}", value))
        elif value:
            values.append((f"work_attributes.{field}", value))
    values.extend((f"contact.{field}", value) for field, value in contact.items())
    return [make_claim(field, value, observed_at, method, confidence) for field, value in values]


def source_link_from_row(row: dict[str, Any], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    url = normalize_space(row.get("source_url"))
    if not url:
        return []
    confidence = normalize_space(row.get("confidence")).casefold() or "unknown"
    if confidence not in CONFIDENCE_VALUES:
        confidence = "unknown"
    source_type = normalize_space(row.get("source_type")) or "manual"
    default_policy, _, default_rights = source_policy_for_type(source_type)
    rights_status = normalized_choice(row.get("rights_status"), RIGHTS_STATUS_VALUES, default_rights)
    return [
        {
            "source_id": stable_cafe_id(
                normalize_space(row.get("source_title")) or normalize_space(row.get("name")),
                normalize_space(row.get("source_type")),
                "",
                url,
                prefix="source",
            ),
            "source_type": source_type,
            "url": url,
            "title": normalize_space(row.get("source_title")),
            "retrieved_at": normalize_space(row.get("retrieved_at")),
            "published_at": normalize_space(row.get("published_at")),
            "source_updated_at": "",
            "policy_id": normalize_space(row.get("policy_id")) or default_policy,
            "claims": claims,
            "evidence_fields": [claim["field"] for claim in claims],
            "confidence": confidence,
            "rights_status": rights_status,
            "rights_basis": normalize_space(row.get("rights_basis")),
            "attribution": normalize_space(row.get("attribution")),
            "notes": normalize_space(row.get("confidence_notes")),
        }
    ]


def normalize_manual_row(
    row: dict[str, Any],
    conflict_annotations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    name = normalize_space(row.get("name"))
    city = normalize_space(row.get("city"))
    district = normalize_space(row.get("district"))
    address = normalize_space(row.get("address"))
    branch_name = normalize_space(row.get("branch_name"))
    confidence = normalize_space(row.get("confidence")).casefold() or "unknown"
    if confidence not in CONFIDENCE_VALUES:
        confidence = "unknown"

    work_attributes = {
        "unlimited_time": enum_or_unknown("unlimited_time", row.get("unlimited_time")),
        "outlets": enum_or_unknown("outlets", row.get("outlets")),
        "wifi": enum_or_unknown("wifi", row.get("wifi")),
        "quietness": enum_or_unknown("quietness", row.get("quietness")),
        "seat_comfort": enum_or_unknown("seat_comfort", row.get("seat_comfort")),
        "meeting_suitability": enum_or_unknown("meeting_suitability", row.get("meeting_suitability")),
        "solo_work_suitability": enum_or_unknown("solo_work_suitability", row.get("solo_work_suitability")),
        "study_suitability": enum_or_unknown("study_suitability", row.get("study_suitability")),
        "online_meeting_suitability": enum_or_unknown(
            "online_meeting_suitability",
            row.get("online_meeting_suitability"),
        ),
        "long_stay_suitability": enum_or_unknown("long_stay_suitability", row.get("long_stay_suitability")),
        "opening_hours": normalize_space(row.get("opening_hours")),
        "minimum_order": normalize_space(row.get("minimum_order")),
        "price_level": normalize_space(row.get("price_level")),
        "food_available": enum_or_unknown("food_available", row.get("food_available")),
        "reservation": enum_or_unknown("reservation", row.get("reservation")),
    }

    contact = contact_from_row(row)
    branch_identity_status = normalized_choice(
        row.get("branch_identity_status"),
        BRANCH_IDENTITY_VALUES,
        "unknown",
    )
    operational_status = normalized_choice(
        row.get("operational_status"),
        OPERATIONAL_STATUS_VALUES,
        "unknown",
    )
    conflicts = list(conflict_annotations or [])
    if any(conflict["status"] == "unresolved" and conflict["field"] == "operational_status" for conflict in conflicts):
        operational_status = "conflicted"
    claimed_operational_status = normalized_choice(
        row.get("operational_status"),
        OPERATIONAL_STATUS_VALUES,
        "unknown",
    )
    claims = manual_claims(
        row,
        work_attributes,
        contact,
        branch_identity_status,
        claimed_operational_status,
    )

    return {
        "cafe_id": stable_cafe_id(name, city, district, address),
        "canonical_name": name,
        "aliases": [],
        "branch_name": branch_name,
        "branch_identity_status": branch_identity_status,
        "operational_status": operational_status,
        "city": city,
        "district": district,
        "address": address,
        "coordinates": coordinates_from_values(row.get("lat"), row.get("lng")),
        "external_ids": {},
        "contact": contact,
        "work_attributes": work_attributes,
        "source_links": source_link_from_row(row, claims),
        "field_confidence": {claim["field"]: claim["confidence"] for claim in claims},
        "overall_confidence": confidence,
        "last_verified_at": normalize_space(row.get("verified_at")),
        "conflicts": conflicts,
        "notes": normalize_space(row.get("notes")),
    }


def address_from_osm_tags(tags: dict[str, Any]) -> str:
    parts = [
        tags.get("addr:city"),
        tags.get("addr:district"),
        tags.get("addr:suburb"),
        tags.get("addr:street"),
        tags.get("addr:housenumber"),
    ]
    return normalize_space(" ".join(part for part in parts if part))


def validate_provider_number(
    value: object,
    location: str,
    lower: float,
    upper: float,
) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{location} must be numeric")
    number = float(value)
    if not math.isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{location} is out of range")
    return number


def osm_coordinates(element: dict[str, Any]) -> dict[str, float] | None:
    if "lat" in element or "lon" in element:
        if "lat" not in element or "lon" not in element:
            raise ValueError("OSM element lat and lon must appear together")
        return {
            "lat": validate_provider_number(element["lat"], "OSM element lat", -90, 90),
            "lng": validate_provider_number(element["lon"], "OSM element lon", -180, 180),
        }
    center = element.get("center", {})
    if not isinstance(center, dict):
        raise TypeError("OSM element center must be an object")
    if "lat" not in center and "lon" not in center:
        return None
    if "lat" not in center or "lon" not in center:
        raise ValueError("OSM element center.lat and center.lon must appear together")
    return {
        "lat": validate_provider_number(center["lat"], "OSM element center.lat", -90, 90),
        "lng": validate_provider_number(center["lon"], "OSM element center.lon", -180, 180),
    }


def normalize_osm_element(element: dict[str, Any], retrieved_at: str | None = None) -> dict[str, Any]:
    if not isinstance(element, dict):
        raise TypeError("OSM element must be an object")
    tags = element.get("tags", {})
    if not isinstance(tags, dict):
        raise TypeError("OSM element tags must be an object")
    for tag, value in tags.items():
        if not isinstance(tag, str) or not isinstance(value, str):
            raise TypeError("OSM element tags must contain only string keys and values")
    if tags.get("amenity") != "cafe":
        raise ValueError("OSM element tags.amenity must be 'cafe'")
    osm_type = element.get("type")
    if not isinstance(osm_type, str) or osm_type not in {"node", "way", "relation"}:
        raise ValueError("OSM element type must be node, way, or relation")
    raw_osm_id = element.get("id")
    if not isinstance(raw_osm_id, int) or isinstance(raw_osm_id, bool):
        raise TypeError("OSM element id must be an integer")
    osm_id = str(raw_osm_id)
    if "timestamp" in element:
        timestamp = element["timestamp"]
        if not isinstance(timestamp, str) or not timestamp.strip():
            raise TypeError("OSM element timestamp must be a non-empty string")
        if not is_iso_date_or_datetime(timestamp):
            raise ValueError("OSM element timestamp must be an ISO 8601 date or timezone-aware datetime")
    if not isinstance(retrieved_at, str) or not is_iso_date_or_datetime(retrieved_at):
        raise ValueError("OSM snapshot retrieved_at must be an ISO 8601 date or timezone-aware datetime")
    name = normalize_space(tags.get("name") or tags.get("name:zh") or tags.get("name:en"))
    city = normalize_space(tags.get("addr:city"))
    district = normalize_space(tags.get("addr:district") or tags.get("addr:suburb"))
    address = address_from_osm_tags(tags)
    website = normalize_space(tags.get("website") or tags.get("contact:website"))
    if website and not is_http_url(website):
        website = ""
    phone = normalize_space(tags.get("phone") or tags.get("contact:phone"))
    internet_access = normalize_space(tags.get("internet_access")).casefold()
    wifi = "yes" if internet_access in {"wlan", "wifi", "yes"} else "unknown"
    url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
    retrieved = retrieved_at
    coordinates = osm_coordinates(element)
    opening_hours = normalize_space(tags.get("opening_hours"))
    claim_values: list[tuple[str, object, str]] = []
    for field, value, confidence in [
        ("canonical_name", name, "high"),
        ("city", city, "medium"),
        ("district", district, "medium"),
        ("address", address, "medium"),
        ("coordinates", coordinates, "high"),
        ("contact.website_url", website, "high"),
        ("contact.phone", phone, "high"),
        ("work_attributes.opening_hours", opening_hours, "medium"),
        ("work_attributes.wifi", wifi if wifi == "yes" else "", "medium"),
    ]:
        if value is not None and (not isinstance(value, str) or value):
            claim_values.append((field, value, confidence))
    claims = [
        make_claim(field, value, "", "dataset_snapshot", confidence)
        for field, value, confidence in claim_values
    ]
    evidence_fields = [claim["field"] for claim in claims]

    return {
        "cafe_id": f"osm-{osm_type}-{osm_id}",
        "canonical_name": name or f"Unnamed OSM cafe {osm_type}/{osm_id}",
        "aliases": [value for value in [normalize_space(tags.get("name:en"))] if value and value != name],
        "branch_name": "",
        "branch_identity_status": "unknown",
        "operational_status": "unknown",
        "city": city,
        "district": district,
        "address": address,
        "coordinates": coordinates,
        "external_ids": {"osm": f"{osm_type}/{osm_id}"},
        "contact": {key: value for key, value in {"website_url": website, "phone": phone}.items() if value},
        "work_attributes": {
            "unlimited_time": "unknown",
            "outlets": "unknown",
            "wifi": wifi,
            "quietness": "unknown",
            "seat_comfort": "unknown",
            "meeting_suitability": "unknown",
            "solo_work_suitability": "unknown",
            "study_suitability": "unknown",
            "online_meeting_suitability": "unknown",
            "long_stay_suitability": "unknown",
            "opening_hours": opening_hours,
            "minimum_order": normalize_space(tags.get("minimum_order")),
            "price_level": "",
            "food_available": "unknown",
            "reservation": "unknown",
        },
        "source_links": [
            {
                "source_id": f"osm-{osm_type}-{osm_id}",
                "source_type": "openstreetmap",
                "url": url,
                "title": f"OpenStreetMap {osm_type}/{osm_id}",
                "retrieved_at": retrieved,
                "published_at": "",
                "source_updated_at": element.get("timestamp", ""),
                "policy_id": "osm_odbl_discovery_v1",
                "claims": claims,
                "evidence_fields": evidence_fields,
                "confidence": "high",
                "rights_status": "attribution_required",
                "rights_basis": "Open Database License (ODbL) 1.0",
                "attribution": "© OpenStreetMap contributors",
                "notes": "Structured OSM POI; work-friendly details may be absent.",
            }
        ],
        "field_confidence": {claim["field"]: claim["confidence"] for claim in claims},
        "overall_confidence": "medium" if name and coordinates is not None else "low",
        "last_verified_at": "",
        "conflicts": [],
        "notes": "Imported from OSM; needs work-friendly enrichment.",
    }


def normalize_google_place(place: dict[str, Any], retrieved_at: str | None = None) -> dict[str, Any]:
    if not isinstance(place, dict):
        raise TypeError("Google Place must be an object")
    for field in [
        "id",
        "name",
        "formattedAddress",
        "websiteUri",
        "googleMapsUri",
        "priceLevel",
    ]:
        if field in place and not isinstance(place[field], str):
            raise TypeError(f"Google Place {field} must be a string")
    if "types" in place and (
        not isinstance(place["types"], list)
        or not all(isinstance(place_type, str) for place_type in place["types"])
    ):
        raise TypeError("Google Place types must be a list of strings")
    if "rating" in place:
        rating = place["rating"]
        if not isinstance(rating, (int, float)) or isinstance(rating, bool):
            raise TypeError("Google Place rating must be numeric")
        if not math.isfinite(float(rating)) or not 0 <= float(rating) <= 5:
            raise ValueError("Google Place rating is out of range")
    if "userRatingCount" in place:
        rating_count = place["userRatingCount"]
        if not isinstance(rating_count, int) or isinstance(rating_count, bool) or rating_count < 0:
            raise TypeError("Google Place userRatingCount must be a nonnegative integer")
    display = place.get("displayName", {})
    if not isinstance(display, dict):
        raise TypeError("Google Place displayName must be an object")
    if "text" in display and not isinstance(display["text"], str):
        raise TypeError("Google Place displayName.text must be a string")
    name = normalize_space(display.get("text") or place.get("name") or place.get("id"))
    location = place.get("location", {})
    if not isinstance(location, dict):
        raise TypeError("Google Place location must be an object")
    if "latitude" in location or "longitude" in location:
        if "latitude" not in location or "longitude" not in location:
            raise ValueError("Google Place latitude and longitude must appear together")
        coordinates = {
            "lat": validate_provider_number(location["latitude"], "Google Place latitude", -90, 90),
            "lng": validate_provider_number(location["longitude"], "Google Place longitude", -180, 180),
        }
    else:
        coordinates = None
    hours = place.get("regularOpeningHours", {})
    if not isinstance(hours, dict):
        raise TypeError("Google Place regularOpeningHours must be an object")
    weekday_descriptions = hours.get("weekdayDescriptions", [])
    if not isinstance(weekday_descriptions, list) or not all(
        isinstance(description, str) for description in weekday_descriptions
    ):
        raise TypeError("Google Place weekdayDescriptions must be a list of strings")
    google_id = normalize_space(place.get("id") or place.get("name"))
    if not isinstance(retrieved_at, str) or not is_iso_date_or_datetime(retrieved_at):
        raise ValueError("Google Places snapshot retrieved_at must be an ISO 8601 date or timezone-aware datetime")
    retrieved = retrieved_at
    address = normalize_space(place.get("formattedAddress"))
    opening_hours = "; ".join(weekday_descriptions)
    price_level = normalize_space(place.get("priceLevel"))
    website_url = normalize_space(place.get("websiteUri"))
    google_maps_url = normalize_space(place.get("googleMapsUri"))
    claim_values = [
        ("canonical_name", name),
        ("address", address),
        ("coordinates", coordinates),
        ("contact.website_url", website_url),
        ("contact.google_maps_url", google_maps_url),
        ("work_attributes.opening_hours", opening_hours),
        ("work_attributes.price_level", price_level),
    ]
    claims = [
        make_claim(field, value, "", "provider_api", "high")
        for field, value in claim_values
        if value is not None and (not isinstance(value, str) or value)
    ]
    evidence_fields = [claim["field"] for claim in claims]

    return {
        "cafe_id": f"google-{hashlib.sha1(google_id.encode('utf-8')).hexdigest()[:12]}",
        "canonical_name": name,
        "aliases": [],
        "branch_name": "",
        "branch_identity_status": "unknown",
        "operational_status": "unknown",
        "city": "",
        "district": "",
        "address": address,
        "coordinates": coordinates,
        "external_ids": {"google_place_id": google_id},
        "contact": {
            key: value
            for key, value in {
                "website_url": website_url,
                "google_maps_url": google_maps_url,
            }.items()
            if value
        },
        "work_attributes": {
            "unlimited_time": "unknown",
            "outlets": "unknown",
            "wifi": "unknown",
            "quietness": "unknown",
            "seat_comfort": "unknown",
            "meeting_suitability": "unknown",
            "solo_work_suitability": "unknown",
            "study_suitability": "unknown",
            "online_meeting_suitability": "unknown",
            "long_stay_suitability": "unknown",
            "opening_hours": opening_hours,
            "minimum_order": "",
            "price_level": price_level,
            "food_available": "unknown",
            "reservation": "unknown",
        },
        "source_links": [
            {
                "source_id": f"google-{hashlib.sha1(google_id.encode('utf-8')).hexdigest()[:12]}",
                "source_type": "google_places",
                "url": normalize_space(place.get("googleMapsUri")) or "https://maps.google.com/",
                "title": f"Google Places: {name}",
                "retrieved_at": retrieved,
                "published_at": "",
                "source_updated_at": "",
                "policy_id": "google_places_restricted_v1",
                "claims": claims,
                "evidence_fields": evidence_fields,
                "confidence": "high",
                "rights_status": "restricted",
                "rights_basis": "Google Maps Platform Terms",
                "attribution": "Google Maps",
                "notes": "Non-production Google Places result; storage and display are policy-restricted.",
            }
        ],
        "field_confidence": {claim["field"]: claim["confidence"] for claim in claims},
        "overall_confidence": "high",
        "last_verified_at": "",
        "conflicts": [],
        "notes": "Non-production Google Places candidate; needs independent work-friendly verification.",
    }
