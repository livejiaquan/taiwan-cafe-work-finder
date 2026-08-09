from __future__ import annotations

import hashlib
import re
from typing import Any

from .schema import WORK_ATTRIBUTE_ENUMS, today_iso


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
    "confidence",
    "confidence_notes",
    "notes",
]


def normalize_space(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable_cafe_id(name: str, city: str, district: str, address: str, prefix: str = "manual") -> str:
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


def field_confidence(confidence: str) -> dict[str, str]:
    normalized = normalize_space(confidence).casefold() or "unknown"
    if normalized not in {"high", "medium", "low", "unknown"}:
        normalized = "unknown"
    return {
        "unlimited_time": normalized,
        "outlets": normalized,
        "wifi": normalized,
        "quietness": normalized,
        "seat_comfort": normalized,
        "meeting_suitability": normalized,
        "solo_work_suitability": normalized,
        "study_suitability": normalized,
        "online_meeting_suitability": normalized,
        "long_stay_suitability": normalized,
        "opening_hours": normalized,
        "minimum_order": normalized,
        "price_level": normalized,
    }


def source_link_from_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    url = normalize_space(row.get("source_url"))
    if not url:
        return []
    confidence = normalize_space(row.get("confidence")).casefold() or "unknown"
    if confidence not in {"high", "medium", "low", "unknown"}:
        confidence = "unknown"
    evidence_fields = []
    for key in [
        "unlimited_time",
        "outlets",
        "wifi",
        "quietness",
        "opening_hours",
        "minimum_order",
        "address",
    ]:
        value = normalize_space(row.get(key))
        if value and value.casefold() != "unknown":
            evidence_fields.append(key)
    return [
        {
            "source_id": stable_cafe_id(
                normalize_space(row.get("source_title")) or normalize_space(row.get("name")),
                normalize_space(row.get("source_type")),
                "",
                url,
                prefix="source",
            ),
            "source_type": normalize_space(row.get("source_type")) or "manual",
            "url": url,
            "title": normalize_space(row.get("source_title")),
            "retrieved_at": normalize_space(row.get("retrieved_at")) or today_iso(),
            "published_at": normalize_space(row.get("published_at")),
            "evidence_fields": evidence_fields,
            "confidence": confidence,
            "notes": normalize_space(row.get("confidence_notes")),
        }
    ]


def normalize_manual_row(row: dict[str, Any]) -> dict[str, Any]:
    name = normalize_space(row.get("name"))
    city = normalize_space(row.get("city"))
    district = normalize_space(row.get("district"))
    address = normalize_space(row.get("address"))
    confidence = normalize_space(row.get("confidence")).casefold() or "unknown"
    if confidence not in {"high", "medium", "low", "unknown"}:
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

    return {
        "cafe_id": stable_cafe_id(name, city, district, address),
        "canonical_name": name,
        "aliases": [],
        "branch_name": normalize_space(row.get("branch_name")),
        "city": city,
        "district": district,
        "address": address,
        "coordinates": coordinates_from_values(row.get("lat"), row.get("lng")),
        "external_ids": {},
        "contact": contact_from_row(row),
        "work_attributes": work_attributes,
        "source_links": source_link_from_row(row),
        "field_confidence": field_confidence(confidence),
        "overall_confidence": confidence,
        "last_verified_at": normalize_space(row.get("retrieved_at")) or today_iso(),
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
    return normalize_space(" ".join(str(part) for part in parts if part))


def osm_coordinates(element: dict[str, Any]) -> dict[str, float] | None:
    if "lat" in element and "lon" in element:
        return coordinates_from_values(element.get("lat"), element.get("lon"))
    center = element.get("center") or {}
    return coordinates_from_values(center.get("lat"), center.get("lon"))


def normalize_osm_element(element: dict[str, Any], retrieved_at: str | None = None) -> dict[str, Any]:
    tags = element.get("tags") or {}
    osm_type = element.get("type", "node")
    osm_id = str(element.get("id", ""))
    name = normalize_space(tags.get("name") or tags.get("name:zh") or tags.get("name:en"))
    city = normalize_space(tags.get("addr:city"))
    district = normalize_space(tags.get("addr:district") or tags.get("addr:suburb"))
    address = address_from_osm_tags(tags)
    website = normalize_space(tags.get("website") or tags.get("contact:website"))
    phone = normalize_space(tags.get("phone") or tags.get("contact:phone"))
    internet_access = normalize_space(tags.get("internet_access")).casefold()
    wifi = "yes" if internet_access in {"wlan", "wifi", "yes"} else "unknown"
    url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
    retrieved = retrieved_at or today_iso()

    return {
        "cafe_id": f"osm-{osm_type}-{osm_id}",
        "canonical_name": name or f"Unnamed OSM cafe {osm_type}/{osm_id}",
        "aliases": [value for value in [normalize_space(tags.get("name:en"))] if value and value != name],
        "branch_name": "",
        "city": city,
        "district": district,
        "address": address,
        "coordinates": osm_coordinates(element),
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
            "opening_hours": normalize_space(tags.get("opening_hours")),
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
                "evidence_fields": ["name", "coordinates", "address", "opening_hours"],
                "confidence": "high",
                "notes": "Structured OSM POI; work-friendly details may be absent.",
            }
        ],
        "field_confidence": {
            "coordinates": "high",
            "address": "medium" if address else "unknown",
            "opening_hours": "medium" if tags.get("opening_hours") else "unknown",
            "wifi": "medium" if wifi == "yes" else "unknown",
            "unlimited_time": "unknown",
            "outlets": "unknown",
            "quietness": "unknown",
        },
        "overall_confidence": "medium",
        "last_verified_at": retrieved,
        "notes": "Imported from OSM; needs work-friendly enrichment.",
    }


def normalize_google_place(place: dict[str, Any], retrieved_at: str | None = None) -> dict[str, Any]:
    display = place.get("displayName") or {}
    name = normalize_space(display.get("text") or place.get("name") or place.get("id"))
    location = place.get("location") or {}
    hours = place.get("regularOpeningHours") or {}
    weekday_descriptions = hours.get("weekdayDescriptions") or []
    google_id = normalize_space(place.get("id") or place.get("name"))
    retrieved = retrieved_at or today_iso()

    return {
        "cafe_id": f"google-{hashlib.sha1(google_id.encode('utf-8')).hexdigest()[:12]}",
        "canonical_name": name,
        "aliases": [],
        "branch_name": "",
        "city": "",
        "district": "",
        "address": normalize_space(place.get("formattedAddress")),
        "coordinates": coordinates_from_values(location.get("latitude"), location.get("longitude")),
        "external_ids": {"google_place_id": google_id},
        "contact": {
            key: value
            for key, value in {
                "website_url": normalize_space(place.get("websiteUri")),
                "google_maps_url": normalize_space(place.get("googleMapsUri")),
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
            "opening_hours": "; ".join(weekday_descriptions),
            "minimum_order": "",
            "price_level": normalize_space(place.get("priceLevel")),
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
                "evidence_fields": ["name", "address", "coordinates", "opening_hours", "price_level"],
                "confidence": "high",
                "notes": "Structured Google Places result; requires API key and billing.",
            }
        ],
        "field_confidence": {
            "coordinates": "high" if location else "unknown",
            "address": "high" if place.get("formattedAddress") else "unknown",
            "opening_hours": "high" if weekday_descriptions else "unknown",
            "price_level": "high" if place.get("priceLevel") else "unknown",
            "unlimited_time": "unknown",
            "outlets": "unknown",
            "wifi": "unknown",
            "quietness": "unknown",
        },
        "overall_confidence": "high",
        "last_verified_at": retrieved,
        "notes": "Imported from Google Places; needs work-friendly enrichment.",
    }
