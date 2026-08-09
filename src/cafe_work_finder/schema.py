from __future__ import annotations

from datetime import date
from urllib.parse import urlparse


CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}

WORK_ATTRIBUTE_ENUMS = {
    "unlimited_time": {"yes", "no", "limited", "conditional", "unknown"},
    "outlets": {"abundant", "some", "limited", "none", "unknown"},
    "wifi": {"yes", "no", "unknown"},
    "quietness": {"quiet", "moderate", "lively", "noisy", "unknown"},
    "seat_comfort": {"good", "fair", "poor", "unknown"},
    "meeting_suitability": {"high", "medium", "low", "unknown"},
    "solo_work_suitability": {"high", "medium", "low", "unknown"},
    "study_suitability": {"high", "medium", "low", "unknown"},
    "online_meeting_suitability": {"high", "medium", "low", "unknown"},
    "long_stay_suitability": {"high", "medium", "low", "unknown"},
    "food_available": {"yes", "no", "unknown"},
    "reservation": {"yes", "no", "unknown"},
}

WORK_ATTRIBUTE_TEXT_FIELDS = {
    "opening_hours",
    "minimum_order",
    "price_level",
}

REQUIRED_RECORD_FIELDS = {
    "cafe_id",
    "canonical_name",
    "aliases",
    "branch_name",
    "city",
    "district",
    "address",
    "coordinates",
    "external_ids",
    "contact",
    "work_attributes",
    "source_links",
    "field_confidence",
    "overall_confidence",
    "last_verified_at",
    "notes",
}


def today_iso() -> str:
    return date.today().isoformat()


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_coordinates(coordinates: object) -> None:
    if coordinates is None:
        return
    require(isinstance(coordinates, dict), "coordinates must be an object or null")
    lat = coordinates.get("lat")
    lng = coordinates.get("lng")
    require(isinstance(lat, (int, float)), "coordinates.lat must be numeric")
    require(isinstance(lng, (int, float)), "coordinates.lng must be numeric")
    require(-90 <= float(lat) <= 90, "coordinates.lat out of range")
    require(-180 <= float(lng) <= 180, "coordinates.lng out of range")


def validate_work_attributes(work_attributes: object) -> None:
    require(isinstance(work_attributes, dict), "work_attributes must be an object")
    for field, allowed in WORK_ATTRIBUTE_ENUMS.items():
        require(field in work_attributes, f"work_attributes.{field} is required")
        require(
            work_attributes[field] in allowed,
            f"work_attributes.{field} has invalid value {work_attributes[field]!r}",
        )
    for field in WORK_ATTRIBUTE_TEXT_FIELDS:
        require(field in work_attributes, f"work_attributes.{field} is required")
        require(
            isinstance(work_attributes[field], str),
            f"work_attributes.{field} must be a string",
        )


def validate_sources(source_links: object) -> None:
    require(isinstance(source_links, list), "source_links must be a list")
    require(len(source_links) > 0, "at least one source link is required")
    for index, source in enumerate(source_links):
        require(isinstance(source, dict), f"source_links[{index}] must be an object")
        url = source.get("url", "")
        require(is_http_url(url), f"source_links[{index}].url must be http(s)")
        require(source.get("source_type"), f"source_links[{index}].source_type is required")
        confidence = source.get("confidence", "unknown")
        require(
            confidence in CONFIDENCE_VALUES,
            f"source_links[{index}].confidence has invalid value {confidence!r}",
        )
        evidence_fields = source.get("evidence_fields", [])
        require(
            isinstance(evidence_fields, list),
            f"source_links[{index}].evidence_fields must be a list",
        )


def validate_record(record: object) -> bool:
    require(isinstance(record, dict), "record must be an object")
    missing = sorted(REQUIRED_RECORD_FIELDS - set(record))
    require(not missing, f"record missing required fields: {', '.join(missing)}")
    require(bool(str(record["cafe_id"]).strip()), "cafe_id is required")
    require(bool(str(record["canonical_name"]).strip()), "canonical_name is required")
    require(isinstance(record["aliases"], list), "aliases must be a list")
    require(isinstance(record["external_ids"], dict), "external_ids must be an object")
    require(isinstance(record["contact"], dict), "contact must be an object")
    require(
        record["overall_confidence"] in CONFIDENCE_VALUES,
        f"overall_confidence has invalid value {record['overall_confidence']!r}",
    )
    require(
        bool(str(record["last_verified_at"]).strip()),
        "last_verified_at is required",
    )
    validate_coordinates(record["coordinates"])
    validate_work_attributes(record["work_attributes"])
    validate_sources(record["source_links"])
    require(isinstance(record["field_confidence"], dict), "field_confidence must be an object")
    for field, confidence in record["field_confidence"].items():
        require(
            confidence in CONFIDENCE_VALUES,
            f"field_confidence.{field} has invalid value {confidence!r}",
        )
    return True

