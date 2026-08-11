from __future__ import annotations

from datetime import date, datetime
import math
import re
from urllib.parse import urlparse

from .source_policy import VERIFICATION_METHODS, validate_source_policy


CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}
BRANCH_IDENTITY_VALUES = {"resolved", "ambiguous", "unknown"}
OPERATIONAL_STATUS_VALUES = {"open", "temporarily_closed", "closed", "conflicted", "unknown"}
RIGHTS_STATUS_VALUES = {"cleared", "attribution_required", "restricted", "unknown"}

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

CONTACT_URL_FIELDS = {
    "website_url",
    "instagram_url",
    "facebook_url",
    "threads_url",
    "google_maps_url",
}
CONTACT_FIELDS = CONTACT_URL_FIELDS | {"phone"}

EVIDENCE_FIELD_VALUES = {
    "canonical_name",
    "branch_name",
    "branch_identity_status",
    "city",
    "district",
    "address",
    "coordinates",
    "operational_status",
} | {
    f"work_attributes.{field}"
    for field in set(WORK_ATTRIBUTE_ENUMS) | WORK_ATTRIBUTE_TEXT_FIELDS
} | {
    f"contact.{field}" for field in CONTACT_FIELDS
}

REQUIRED_RECORD_FIELDS = {
    "cafe_id",
    "canonical_name",
    "aliases",
    "branch_name",
    "branch_identity_status",
    "operational_status",
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
    "conflicts",
    "notes",
}

REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "source_type",
    "url",
    "title",
    "retrieved_at",
    "published_at",
    "source_updated_at",
    "policy_id",
    "claims",
    "evidence_fields",
    "confidence",
    "rights_status",
    "rights_basis",
    "attribution",
    "notes",
}

REQUIRED_CLAIM_FIELDS = {
    "field",
    "value",
    "observed_at",
    "verification_method",
    "confidence",
}

REQUIRED_CONFLICT_FIELDS = {"conflict_id", "field", "status", "summary", "signals"}
REQUIRED_CONFLICT_SIGNAL_FIELDS = {
    "source_type",
    "url",
    "retrieved_at",
    "reported_value",
    "notes",
}

TOP_LEVEL_STRING_FIELDS = {
    "cafe_id",
    "canonical_name",
    "branch_name",
    "city",
    "district",
    "address",
    "last_verified_at",
    "notes",
}

_ISO_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T.*)?$")


def today_iso() -> str:
    return date.today().isoformat()


def is_http_url(value: str) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_iso_date_or_datetime(value: str) -> bool:
    if not isinstance(value, str) or not _ISO_PREFIX.fullmatch(value):
        return False
    try:
        if "T" not in value:
            date.fromisoformat(value)
            return True
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def validate_optional_date(value: object, field: str) -> None:
    require(isinstance(value, str), f"{field} must be a string")
    if value:
        require(is_iso_date_or_datetime(value), f"{field} must be an ISO 8601 date or datetime")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_exact_keys(value: dict, expected: set[str], location: str) -> None:
    missing = sorted(expected - set(value))
    require(not missing, f"{location} missing required fields: {', '.join(missing)}")
    unknown = sorted(set(value) - expected, key=repr)
    require(
        not unknown,
        f"{location} has unknown fields: {', '.join(repr(field) for field in unknown)}",
    )


def validate_unique_cafe_ids(records: list[dict], location: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for index, record in enumerate(records):
        require(isinstance(record, dict), f"{location}[{index}] must be an object")
        cafe_id = record.get("cafe_id")
        require(isinstance(cafe_id, str) and bool(cafe_id.strip()), f"{location}[{index}].cafe_id is required")
        if cafe_id in seen:
            duplicates.add(cafe_id)
        seen.add(cafe_id)
    require(
        not duplicates,
        f"{location} contains duplicate cafe_id values: {', '.join(repr(value) for value in sorted(duplicates))}",
    )


def validate_coordinates(coordinates: object) -> None:
    if coordinates is None:
        return
    require(isinstance(coordinates, dict), "coordinates must be an object or null")
    require_exact_keys(coordinates, {"lat", "lng"}, "coordinates")
    lat = coordinates.get("lat")
    lng = coordinates.get("lng")
    require(isinstance(lat, (int, float)) and not isinstance(lat, bool), "coordinates.lat must be numeric")
    require(isinstance(lng, (int, float)) and not isinstance(lng, bool), "coordinates.lng must be numeric")
    require(math.isfinite(float(lat)), "coordinates.lat must be finite")
    require(math.isfinite(float(lng)), "coordinates.lng must be finite")
    require(-90 <= float(lat) <= 90, "coordinates.lat out of range")
    require(-180 <= float(lng) <= 180, "coordinates.lng out of range")


def validate_work_attributes(work_attributes: object) -> None:
    require(isinstance(work_attributes, dict), "work_attributes must be an object")
    require_exact_keys(
        work_attributes,
        set(WORK_ATTRIBUTE_ENUMS) | WORK_ATTRIBUTE_TEXT_FIELDS,
        "work_attributes",
    )
    for field, allowed in WORK_ATTRIBUTE_ENUMS.items():
        require(field in work_attributes, f"work_attributes.{field} is required")
        require(
            isinstance(work_attributes[field], str),
            f"work_attributes.{field} must be a string",
        )
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


def validate_contact(contact: object) -> None:
    require(isinstance(contact, dict), "contact must be an object")
    unknown = sorted(set(contact) - CONTACT_FIELDS)
    require(not unknown, f"contact has unknown fields: {', '.join(unknown)}")
    for field, value in contact.items():
        require(isinstance(value, str), f"contact.{field} must be a string")
        require(bool(value.strip()), f"contact.{field} must not be empty")
        if field in CONTACT_URL_FIELDS:
            require(is_http_url(value), f"contact.{field} must be http(s)")


def validate_sources(source_links: object) -> set[str]:
    require(isinstance(source_links, list), "source_links must be a list")
    require(len(source_links) > 0, "at least one source link is required")
    all_evidence_fields: set[str] = set()
    source_ids: set[str] = set()
    for index, source in enumerate(source_links):
        require(isinstance(source, dict), f"source_links[{index}] must be an object")
        require_exact_keys(source, REQUIRED_SOURCE_FIELDS, f"source_links[{index}]")
        for field in [
            "source_id",
            "source_type",
            "url",
            "title",
            "retrieved_at",
            "published_at",
            "source_updated_at",
            "policy_id",
            "rights_basis",
            "attribution",
            "notes",
        ]:
            require(isinstance(source[field], str), f"source_links[{index}].{field} must be a string")
        require(bool(source["source_id"].strip()), f"source_links[{index}].source_id is required")
        require(source["source_id"] not in source_ids, f"duplicate source_id {source['source_id']!r}")
        source_ids.add(source["source_id"])
        require(bool(source["source_type"].strip()), f"source_links[{index}].source_type is required")
        url = source["url"]
        require(is_http_url(url), f"source_links[{index}].url must be http(s)")
        require(
            is_iso_date_or_datetime(source["retrieved_at"]),
            f"source_links[{index}].retrieved_at must be an ISO 8601 date or datetime",
        )
        for field in ["published_at", "source_updated_at"]:
            validate_optional_date(source[field], f"source_links[{index}].{field}")
        confidence = source["confidence"]
        require(isinstance(confidence, str), f"source_links[{index}].confidence must be a string")
        require(
            confidence in CONFIDENCE_VALUES,
            f"source_links[{index}].confidence has invalid value {confidence!r}",
        )
        rights_status = source["rights_status"]
        require(isinstance(rights_status, str), f"source_links[{index}].rights_status must be a string")
        require(
            rights_status in RIGHTS_STATUS_VALUES,
            f"source_links[{index}].rights_status has invalid value {rights_status!r}",
        )
        if rights_status in {"cleared", "attribution_required", "restricted"}:
            require(bool(source["rights_basis"].strip()), f"source_links[{index}].rights_basis is required")
        if rights_status == "attribution_required":
            require(bool(source["attribution"].strip()), f"source_links[{index}].attribution is required")
        claims = source["claims"]
        require(isinstance(claims, list), f"source_links[{index}].claims must be a list")
        require(bool(claims), f"source_links[{index}].claims must not be empty")
        claim_fields: list[str] = []
        for claim_index, claim in enumerate(claims):
            require(isinstance(claim, dict), f"source_links[{index}].claims[{claim_index}] must be an object")
            require_exact_keys(
                claim,
                REQUIRED_CLAIM_FIELDS,
                f"source_links[{index}].claims[{claim_index}]",
            )
            field = claim["field"]
            require(isinstance(field, str), f"source_links[{index}].claims[{claim_index}].field must be a string")
            require(
                field in EVIDENCE_FIELD_VALUES,
                f"source_links[{index}].claims[{claim_index}].field is unknown: {field!r}",
            )
            validate_claim_value(field, claim["value"], f"source_links[{index}].claims[{claim_index}].value")
            validate_optional_date(
                claim["observed_at"],
                f"source_links[{index}].claims[{claim_index}].observed_at",
            )
            method = claim["verification_method"]
            require(
                isinstance(method, str) and method in VERIFICATION_METHODS,
                f"source_links[{index}].claims[{claim_index}].verification_method is invalid: {method!r}",
            )
            claim_confidence = claim["confidence"]
            require(
                isinstance(claim_confidence, str) and claim_confidence in CONFIDENCE_VALUES,
                f"source_links[{index}].claims[{claim_index}].confidence is invalid: {claim_confidence!r}",
            )
            claim_fields.append(field)
        require(
            len(claim_fields) == len(set(claim_fields)),
            f"source_links[{index}].claims fields must be unique",
        )
        evidence_fields = source["evidence_fields"]
        require(
            isinstance(evidence_fields, list),
            f"source_links[{index}].evidence_fields must be a list",
        )
        require(
            all(isinstance(field, str) for field in evidence_fields),
            f"source_links[{index}].evidence_fields must contain strings",
        )
        unknown_fields = sorted(set(evidence_fields) - EVIDENCE_FIELD_VALUES)
        require(
            not unknown_fields,
            f"source_links[{index}].evidence_fields has unknown fields: {', '.join(unknown_fields)}",
        )
        require(
            len(evidence_fields) == len(set(evidence_fields)),
            f"source_links[{index}].evidence_fields must not contain duplicates",
        )
        require(
            set(evidence_fields) == set(claim_fields),
            f"source_links[{index}].evidence_fields must exactly match claims fields",
        )
        validate_source_policy(source, index)
        all_evidence_fields.update(evidence_fields)
    return all_evidence_fields


def validate_claim_value(field: str, value: object, location: str) -> None:
    if field == "coordinates":
        require(value is not None, f"{location} must not be null")
        try:
            validate_coordinates(value)
        except ValueError as exc:
            raise ValueError(f"{location}: {exc}") from exc
        return
    if field == "branch_identity_status":
        require(isinstance(value, str) and value in BRANCH_IDENTITY_VALUES, f"{location} is invalid")
        return
    if field == "operational_status":
        require(isinstance(value, str) and value in OPERATIONAL_STATUS_VALUES, f"{location} is invalid")
        return
    if field.startswith("work_attributes."):
        attribute = field.split(".", 1)[1]
        if attribute in WORK_ATTRIBUTE_ENUMS:
            require(
                isinstance(value, str) and value in WORK_ATTRIBUTE_ENUMS[attribute],
                f"{location} is invalid for {field}",
            )
        else:
            require(isinstance(value, str) and bool(value.strip()), f"{location} must be a non-empty string")
        return
    if field.startswith("contact."):
        contact_field = field.split(".", 1)[1]
        require(isinstance(value, str) and bool(value.strip()), f"{location} must be a non-empty string")
        if contact_field in CONTACT_URL_FIELDS:
            require(is_http_url(value), f"{location} must be http(s)")
        return
    require(isinstance(value, str) and bool(value.strip()), f"{location} must be a non-empty string")


def validate_conflicts(conflicts: object) -> None:
    require(isinstance(conflicts, list), "conflicts must be a list")
    conflict_ids: set[str] = set()
    for index, conflict in enumerate(conflicts):
        require(isinstance(conflict, dict), f"conflicts[{index}] must be an object")
        require_exact_keys(conflict, REQUIRED_CONFLICT_FIELDS, f"conflicts[{index}]")
        for field in ["conflict_id", "field", "status", "summary"]:
            require(isinstance(conflict[field], str) and conflict[field].strip(), f"conflicts[{index}].{field} is required")
        require(conflict["conflict_id"] not in conflict_ids, f"duplicate conflict_id {conflict['conflict_id']!r}")
        conflict_ids.add(conflict["conflict_id"])
        require(conflict["field"] in EVIDENCE_FIELD_VALUES, f"conflicts[{index}].field is unknown")
        require(conflict["status"] in {"unresolved", "resolved"}, f"conflicts[{index}].status is invalid")
        signals = conflict["signals"]
        require(isinstance(signals, list) and len(signals) >= 2, f"conflicts[{index}].signals needs at least two signals")
        for signal_index, signal in enumerate(signals):
            require(isinstance(signal, dict), f"conflicts[{index}].signals[{signal_index}] must be an object")
            require_exact_keys(
                signal,
                REQUIRED_CONFLICT_SIGNAL_FIELDS,
                f"conflicts[{index}].signals[{signal_index}]",
            )
            for field in ["source_type", "url", "retrieved_at", "reported_value", "notes"]:
                require(isinstance(signal[field], str), f"conflicts[{index}].signals[{signal_index}].{field} must be a string")
            require(bool(signal["source_type"].strip()), f"conflicts[{index}].signals[{signal_index}].source_type is required")
            require(is_http_url(signal["url"]), f"conflicts[{index}].signals[{signal_index}].url must be http(s)")
            require(
                is_iso_date_or_datetime(signal["retrieved_at"]),
                f"conflicts[{index}].signals[{signal_index}].retrieved_at must be ISO 8601",
            )
            require(bool(signal["reported_value"].strip()), f"conflicts[{index}].signals[{signal_index}].reported_value is required")


def validate_conflict_registry(entries: object) -> None:
    require(isinstance(entries, list), "conflict registry must be a list")
    for index, entry in enumerate(entries):
        require(isinstance(entry, dict), f"conflict registry[{index}] must be an object")
        require_exact_keys(entry, {"match", "conflict"}, f"conflict registry[{index}]")
        match = entry["match"]
        require(isinstance(match, dict), f"conflict registry[{index}].match must be an object")
        require_exact_keys(
            match,
            {"canonical_name", "source_url"},
            f"conflict registry[{index}].match",
        )
        require(
            isinstance(match.get("canonical_name"), str) and match["canonical_name"].strip(),
            f"conflict registry[{index}].match.canonical_name is required",
        )
        require(
            isinstance(match.get("source_url"), str) and is_http_url(match["source_url"]),
            f"conflict registry[{index}].match.source_url must be http(s)",
        )
        validate_conflicts([entry["conflict"]])


def validate_record(record: object) -> bool:
    require(isinstance(record, dict), "record must be an object")
    require_exact_keys(record, REQUIRED_RECORD_FIELDS, "record")
    for field in TOP_LEVEL_STRING_FIELDS:
        require(isinstance(record[field], str), f"{field} must be a string")
    require(bool(record["cafe_id"].strip()), "cafe_id is required")
    require(bool(record["canonical_name"].strip()), "canonical_name is required")
    require(isinstance(record["aliases"], list), "aliases must be a list")
    require(all(isinstance(alias, str) for alias in record["aliases"]), "aliases must contain strings")
    require(isinstance(record["branch_identity_status"], str), "branch_identity_status must be a string")
    require(
        record["branch_identity_status"] in BRANCH_IDENTITY_VALUES,
        f"branch_identity_status has invalid value {record['branch_identity_status']!r}",
    )
    require(isinstance(record["operational_status"], str), "operational_status must be a string")
    require(
        record["operational_status"] in OPERATIONAL_STATUS_VALUES,
        f"operational_status has invalid value {record['operational_status']!r}",
    )
    require(isinstance(record["external_ids"], dict), "external_ids must be an object")
    require(
        all(
            isinstance(key, str)
            and bool(key.strip())
            and isinstance(value, str)
            and bool(value.strip())
            for key, value in record["external_ids"].items()
        ),
        "external_ids must contain non-empty string keys and values",
    )
    validate_contact(record["contact"])
    require(isinstance(record["overall_confidence"], str), "overall_confidence must be a string")
    require(
        record["overall_confidence"] in CONFIDENCE_VALUES,
        f"overall_confidence has invalid value {record['overall_confidence']!r}",
    )
    validate_optional_date(record["last_verified_at"], "last_verified_at")
    validate_conflicts(record["conflicts"])
    unresolved_operational_conflict = any(
        conflict["status"] == "unresolved" and conflict["field"] == "operational_status"
        for conflict in record["conflicts"]
    )
    require(
        (record["operational_status"] == "conflicted") == unresolved_operational_conflict,
        "operational_status must be conflicted exactly when an unresolved operational conflict exists",
    )
    validate_coordinates(record["coordinates"])
    validate_work_attributes(record["work_attributes"])
    evidence_fields = validate_sources(record["source_links"])
    require(isinstance(record["field_confidence"], dict), "field_confidence must be an object")
    for field, confidence in record["field_confidence"].items():
        require(isinstance(field, str), "field_confidence keys must be strings")
        require(field in EVIDENCE_FIELD_VALUES, f"field_confidence has unknown field {field!r}")
        require(field in evidence_fields, f"field_confidence.{field} has no supporting source evidence")
        require(isinstance(confidence, str), f"field_confidence.{field} must be a string")
        require(
            confidence in CONFIDENCE_VALUES,
            f"field_confidence.{field} has invalid value {confidence!r}",
        )
    require(
        set(record["field_confidence"]) == evidence_fields,
        "field_confidence keys must exactly match all source claim fields",
    )
    return True
