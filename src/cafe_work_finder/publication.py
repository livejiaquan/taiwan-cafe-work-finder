from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import json
from typing import Any

from .schema import WORK_ATTRIBUTE_ENUMS, WORK_ATTRIBUTE_TEXT_FIELDS, validate_record
from .source_policy import publication_claim_allowed


FRESHNESS_DAYS = {
    "canonical_name": 365,
    "branch_name": 365,
    "branch_identity_status": 365,
    "city": 365,
    "district": 365,
    "address": 365,
    "coordinates": 365,
    "operational_status": 30,
    "contact.website_url": 90,
    "contact.instagram_url": 90,
    "contact.facebook_url": 90,
    "contact.threads_url": 90,
    "contact.google_maps_url": 90,
    "contact.phone": 90,
    "work_attributes.unlimited_time": 30,
    "work_attributes.outlets": 90,
    "work_attributes.wifi": 30,
    "work_attributes.quietness": 30,
    "work_attributes.seat_comfort": 90,
    "work_attributes.meeting_suitability": 30,
    "work_attributes.solo_work_suitability": 30,
    "work_attributes.study_suitability": 30,
    "work_attributes.online_meeting_suitability": 30,
    "work_attributes.long_stay_suitability": 30,
    "work_attributes.opening_hours": 30,
    "work_attributes.minimum_order": 30,
    "work_attributes.price_level": 90,
    "work_attributes.food_available": 30,
    "work_attributes.reservation": 30,
}

REQUIRED_FIELDS = (
    "canonical_name",
    "branch_identity_status",
    "city",
    "district",
    "address",
    "coordinates",
    "operational_status",
)

GREATER_TAIPEI_CITY_ALIASES = {
    "Taipei": "臺北市",
    "Taipei City": "臺北市",
    "台北市": "臺北市",
    "臺北市": "臺北市",
    "New Taipei": "新北市",
    "New Taipei City": "新北市",
    "新北市": "新北市",
}
GREATER_TAIPEI_DISTRICTS = {
    "臺北市": {
        "Beitou", "Shilin", "Zhongshan", "Songshan", "Neihu", "Nangang",
        "Wanhua", "Datong", "Zhongzheng", "Da'an", "Daan", "Xinyi", "Wenshan",
        "北投區", "士林區", "中山區", "松山區", "內湖區", "南港區",
        "萬華區", "大同區", "中正區", "大安區", "信義區", "文山區",
    },
    "新北市": {
        "Banqiao", "Sanchong", "Zhonghe", "Yonghe", "Xinzhuang", "Xindian",
        "Tucheng", "Luzhou", "Shulin", "Yingge", "Sanxia", "Tamsui", "Xizhi",
        "Ruifang", "Wugu", "Taishan", "Linkou", "Shenkeng", "Shiding", "Pinglin",
        "Sanzhi", "Shimen", "Bali", "Pingxi", "Shuangxi", "Gongliao", "Jinshan",
        "Wanli", "Wulai", "板橋區", "三重區", "中和區", "永和區", "新莊區",
        "新店區", "土城區", "蘆洲區", "樹林區", "鶯歌區", "三峽區", "淡水區",
        "汐止區", "瑞芳區", "五股區", "泰山區", "林口區", "深坑區", "石碇區",
        "坪林區", "三芝區", "石門區", "八里區", "平溪區", "雙溪區", "貢寮區",
        "金山區", "萬里區", "烏來區",
    },
}
GREATER_TAIPEI_GEOFENCE = {
    "lat_min": 24.65,
    "lat_max": 25.35,
    "lng_min": 121.25,
    "lng_max": 122.10,
}


def parse_iso_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def parse_audit_date(value: str) -> date:
    if not isinstance(value, str) or "T" in value:
        raise ValueError("publication as-of must be an ISO 8601 date without a time")
    return date.fromisoformat(value)


def parse_iso_temporal(value: str) -> date | datetime:
    if "T" not in value:
        return date.fromisoformat(value)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"datetime must include a timezone offset: {value!r}")
    return parsed.astimezone(timezone.utc)


def chronology_leq(earlier: str, later: str) -> bool:
    """Return true only when the available precision proves earlier <= later."""
    earlier_value = parse_iso_temporal(earlier)
    later_value = parse_iso_temporal(later)
    earlier_is_datetime = isinstance(earlier_value, datetime)
    later_is_datetime = isinstance(later_value, datetime)
    if earlier_is_datetime and later_is_datetime:
        return earlier_value <= later_value
    if not earlier_is_datetime and not later_is_datetime:
        return earlier_value <= later_value
    earlier_date = parse_iso_date(earlier)
    later_date = parse_iso_date(later)
    if earlier_date != later_date:
        return earlier_date < later_date
    return False


def source_rights_ready(source: dict[str, Any]) -> bool:
    if source["rights_status"] == "cleared":
        return bool(source["rights_basis"].strip())
    return (
        source["rights_status"] == "attribution_required"
        and bool(source["rights_basis"].strip())
        and bool(source["attribution"].strip())
    )


def field_value(record: dict[str, Any], field: str) -> object:
    if field.startswith("work_attributes."):
        return record["work_attributes"][field.split(".", 1)[1]]
    if field.startswith("contact."):
        return record["contact"].get(field.split(".", 1)[1], "")
    return record[field]


def field_claims(record: dict[str, Any], field: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    claims: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for source in record["source_links"]:
        claims.extend((source, claim) for claim in source["claims"] if claim["field"] == field)
    return claims


def evaluate_field_evidence(
    record: dict[str, Any],
    field: str,
    as_of: date,
    environment: str,
) -> tuple[str, str]:
    claims = field_claims(record, field)
    if not claims:
        return "unsupported", "no structured claim supports this field"

    canonical_value = field_value(record, field)
    max_age = FRESHNESS_DAYS[field]
    fresh_claims = [
        claim
        for _, claim in claims
        if claim["observed_at"]
        and 0 <= (as_of - parse_iso_date(claim["observed_at"])).days <= max_age
    ]
    mismatches = [claim["value"] for claim in fresh_claims if claim["value"] != canonical_value]
    if mismatches:
        values = [canonical_value, *mismatches]
        rendered = sorted({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values})
        return "value_mismatch", f"claim values disagree with canonical value: {', '.join(rendered)}"

    saw_observation = False
    saw_current = False
    saw_policy = False
    saw_confidence = False
    saw_rights = False
    saw_future = False
    youngest_age: int | None = None

    for source, claim in claims:
        observed_at = claim["observed_at"]
        if not observed_at:
            continue
        saw_observation = True
        age = (as_of - parse_iso_date(observed_at)).days
        if age < 0:
            saw_future = True
            continue
        youngest_age = age if youngest_age is None else min(youngest_age, age)
        if age > max_age:
            continue
        saw_current = True
        if not publication_claim_allowed(source, claim, environment):
            continue
        saw_policy = True
        if (
            source["confidence"] not in {"high", "medium"}
            or claim["confidence"] not in {"high", "medium"}
            or record["field_confidence"].get(field) not in {"high", "medium"}
        ):
            continue
        saw_confidence = True
        if not source_rights_ready(source):
            continue
        saw_rights = True
        return "fresh", f"matching claim observed {age} day(s) ago; limit {max_age}"

    if not saw_observation:
        return "unknown", "retrieval, publication, and source-update times are not observations"
    if youngest_age is None and saw_future:
        return "future", "observation date is after the audit date"
    if not saw_current:
        return "stale", f"youngest observation is {youngest_age} day(s) old; limit {max_age}"
    if not saw_policy:
        return "policy_blocked", "no fresh claim uses a publication-approved source policy and method"
    if not saw_confidence:
        return "confidence_blocked", "source, claim, and field confidence must all be high or medium"
    if not saw_rights:
        return "rights_blocked", "supporting source rights or attribution are not publication-ready"
    return "unsupported", "no publication-ready matching claim"


def known_work_fields(record: dict[str, Any]) -> list[str]:
    attributes = record["work_attributes"]
    fields = [
        f"work_attributes.{field}"
        for field in WORK_ATTRIBUTE_ENUMS
        if attributes[field] != "unknown"
    ]
    fields.extend(
        f"work_attributes.{field}"
        for field in WORK_ATTRIBUTE_TEXT_FIELDS
        if attributes[field].strip()
    )
    return sorted(fields)


def public_optional_fields(record: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    if record["branch_name"].strip():
        fields.append("branch_name")
    fields.extend(f"contact.{field}" for field, value in record["contact"].items() if value.strip())
    return sorted(fields)


def scope_result(record: dict[str, Any]) -> dict[str, Any]:
    normalized_city = GREATER_TAIPEI_CITY_ALIASES.get(record["city"], "")
    district_allowed = bool(
        normalized_city
        and record["district"] in GREATER_TAIPEI_DISTRICTS[normalized_city]
    )
    coordinates = record["coordinates"] or {}
    lat = coordinates.get("lat")
    lng = coordinates.get("lng")
    within_geofence = bool(
        isinstance(lat, (int, float))
        and not isinstance(lat, bool)
        and isinstance(lng, (int, float))
        and not isinstance(lng, bool)
        and GREATER_TAIPEI_GEOFENCE["lat_min"] <= lat <= GREATER_TAIPEI_GEOFENCE["lat_max"]
        and GREATER_TAIPEI_GEOFENCE["lng_min"] <= lng <= GREATER_TAIPEI_GEOFENCE["lng_max"]
    )
    return {
        "city_input": record["city"],
        "city_normalized": normalized_city,
        "city_allowed": bool(normalized_city),
        "district_input": record["district"],
        "district_allowed": district_allowed,
        "coordinates_within_geofence": within_geofence,
    }


def audit_record(
    record: dict[str, Any],
    as_of: str,
    environment: str = "production",
) -> dict[str, Any]:
    validate_record(record)
    if environment not in {"production", "test"}:
        raise ValueError(f"unsupported publication environment: {environment!r}")
    audit_date = parse_audit_date(as_of)
    blockers: list[dict[str, str]] = []
    field_status: dict[str, dict[str, str | int]] = {}

    def block(code: str, field: str, detail: str) -> None:
        blockers.append({"code": code, "field": field, "detail": detail})

    scope = scope_result(record)
    if not scope["city_allowed"]:
        block("outside_city_scope", "city", "city is not in the reviewed Greater Taipei whitelist")
    if not scope["district_allowed"]:
        block("outside_district_scope", "district", "district is not valid for the reviewed Greater Taipei city")
    if not scope["coordinates_within_geofence"]:
        block("outside_geofence", "coordinates", "coordinates are outside the broad Greater Taipei geofence")

    if record["branch_identity_status"] != "resolved":
        block(
            "branch_not_resolved",
            "branch_identity_status",
            "branch identity must be explicitly resolved; a blank branch name alone is not a failure",
        )

    operational_status = record["operational_status"]
    if operational_status != "open":
        code = (
            "operational_status_closed"
            if operational_status in {"closed", "temporarily_closed"}
            else "operational_status_unusable"
        )
        block(code, "operational_status", f"status is {operational_status!r}, not verified open")

    unresolved_conflicts = [conflict for conflict in record["conflicts"] if conflict["status"] == "unresolved"]
    if unresolved_conflicts:
        detail = "; ".join(sorted(conflict["summary"] for conflict in unresolved_conflicts))
        block("unresolved_conflicts", "conflicts", detail)
    resolved_conflicts = [conflict for conflict in record["conflicts"] if conflict["status"] == "resolved"]
    if environment == "production" and resolved_conflicts:
        block(
            "resolved_conflict_provenance_unimplemented",
            "conflicts",
            "resolved conflicts remain production-blocked until resolution provenance is modeled",
        )

    if record["overall_confidence"] not in {"high", "medium"}:
        block("record_confidence_blocked", "overall_confidence", "publication requires high or medium overall confidence")

    last_verified_date: date | None = None
    if not record["last_verified_at"]:
        block("record_verification_missing", "last_verified_at", "retrieval time cannot replace verification time")
    else:
        last_verified_date = parse_iso_date(record["last_verified_at"])
        verified_age = (audit_date - last_verified_date).days
        if verified_age < 0:
            block("record_verification_future", "last_verified_at", "verification date is after the audit date")
        elif verified_age > 30:
            block("record_verification_stale", "last_verified_at", f"record verification is {verified_age} day(s) old")

    for source_index, source in enumerate(record["source_links"]):
        for timestamp_field in ("retrieved_at", "published_at", "source_updated_at"):
            timestamp = source[timestamp_field]
            if timestamp and parse_iso_date(timestamp) > audit_date:
                block(
                    "source_timestamp_future",
                    f"source_links[{source_index}].{timestamp_field}",
                    "source provenance timestamp is after the audit date",
                )
        for timestamp_field in ("published_at", "source_updated_at"):
            timestamp = source[timestamp_field]
            if timestamp and not chronology_leq(timestamp, source["retrieved_at"]):
                block(
                    "source_chronology_invalid",
                    f"source_links[{source_index}].{timestamp_field}",
                    f"{timestamp_field} must be provably at or before retrieved_at",
                )
        if last_verified_date is not None and not chronology_leq(
            source["retrieved_at"],
            record["last_verified_at"],
        ):
            block(
                "source_chronology_invalid",
                f"source_links[{source_index}].retrieved_at",
                "source retrieved_at must be provably at or before record last_verified_at",
            )
        for claim_index, claim in enumerate(source["claims"]):
            if not claim["observed_at"]:
                continue
            observed_date = parse_iso_date(claim["observed_at"])
            if observed_date > audit_date:
                block(
                    "claim_observation_future",
                    f"source_links[{source_index}].claims[{claim_index}].observed_at",
                    "claim observation is after the audit date",
                )
            if not chronology_leq(claim["observed_at"], source["retrieved_at"]):
                block(
                    "source_chronology_invalid",
                    f"source_links[{source_index}].claims[{claim_index}].observed_at",
                    "claim observed_at must be provably at or before source retrieved_at",
                )
    for conflict_index, conflict in enumerate(record["conflicts"]):
        for signal_index, signal in enumerate(conflict["signals"]):
            if parse_iso_date(signal["retrieved_at"]) > audit_date:
                block(
                    "source_timestamp_future",
                    f"conflicts[{conflict_index}].signals[{signal_index}].retrieved_at",
                    "conflict signal retrieval is after the audit date",
                )

    for field in REQUIRED_FIELDS:
        value = field_value(record, field)
        if value is None or (isinstance(value, str) and not value.strip()):
            block("required_value_missing", field, "publication requires a concrete value")
            field_status[field] = {"status": "unknown", "max_age_days": FRESHNESS_DAYS[field]}
            continue
        status, detail = evaluate_field_evidence(record, field, audit_date, environment)
        field_status[field] = {"status": status, "max_age_days": FRESHNESS_DAYS[field], "detail": detail}
        if status != "fresh":
            block(f"evidence_{status}", field, detail)

    attributes = record["work_attributes"]
    if attributes["solo_work_suitability"] not in {"high", "medium"}:
        block(
            "core_condition_missing",
            "work_attributes.solo_work_suitability",
            "quiet solo-work recommendations require high or medium suitability",
        )
    if attributes["quietness"] not in {"quiet", "moderate"}:
        block(
            "core_condition_missing",
            "work_attributes.quietness",
            "quiet solo-work recommendations require quiet or moderate conditions",
        )
    if attributes["online_meeting_suitability"] != "unknown":
        block(
            "out_of_scope_claim",
            "work_attributes.online_meeting_suitability",
            "online-meeting suitability is excluded from the first product scope",
        )
    if attributes["unlimited_time"] == "conditional":
        block(
            "condition_not_modeled",
            "work_attributes.unlimited_time",
            "conditional time limits cannot publish until the actual condition is represented",
        )

    work_fields = known_work_fields(record)
    for field in work_fields:
        status, detail = evaluate_field_evidence(record, field, audit_date, environment)
        field_status[field] = {"status": status, "max_age_days": FRESHNESS_DAYS[field], "detail": detail}
        if status != "fresh":
            block(f"evidence_{status}", field, detail)

    optional_fields = public_optional_fields(record)
    for field in optional_fields:
        status, detail = evaluate_field_evidence(record, field, audit_date, environment)
        field_status[field] = {"status": status, "max_age_days": FRESHNESS_DAYS[field], "detail": detail}
        if status != "fresh":
            block(f"evidence_{status}", field, detail)

    claimed_fields = {
        claim["field"]
        for source in record["source_links"]
        for claim in source["claims"]
    }
    already_audited = set(REQUIRED_FIELDS) | set(work_fields) | set(optional_fields)
    for field in sorted(claimed_fields - already_audited):
        status, detail = evaluate_field_evidence(record, field, audit_date, environment)
        field_status[field] = {"status": status, "max_age_days": FRESHNESS_DAYS[field], "detail": detail}
        if status != "fresh":
            block(f"evidence_{status}", field, detail)

    unique_blockers = {(item["code"], item["field"], item["detail"]): item for item in blockers}
    sorted_blockers = [unique_blockers[key] for key in sorted(unique_blockers)]
    publishable = not sorted_blockers
    if publishable:
        status = "publishable"
    elif operational_status in {"closed", "temporarily_closed"}:
        status = "closed"
    elif (
        unresolved_conflicts
        or operational_status == "conflicted"
        or any(item["code"] == "evidence_value_mismatch" for item in sorted_blockers)
    ):
        status = "conflicted"
    elif any(item["code"] == "evidence_stale" for item in sorted_blockers):
        status = "stale"
    else:
        status = "candidate"

    return {
        "cafe_id": record["cafe_id"],
        "canonical_name": record["canonical_name"],
        "publishable": publishable,
        "status": status,
        "environment": environment,
        "scope": scope,
        "blockers": sorted_blockers,
        "field_status": {field: field_status[field] for field in sorted(field_status)},
    }


def audit_records(
    records: list[dict[str, Any]],
    as_of: str,
    environment: str = "production",
) -> dict[str, Any]:
    if environment not in {"production", "test"}:
        raise ValueError(f"unsupported publication environment: {environment!r}")
    audit_date = parse_audit_date(as_of).isoformat()
    cafe_ids = [record.get("cafe_id") for record in records if isinstance(record, dict)]
    duplicates = sorted(
        (cafe_id for cafe_id, count in Counter(cafe_ids).items() if count > 1),
        key=repr,
    )
    if duplicates:
        raise ValueError(f"dataset contains duplicate cafe_id values: {', '.join(repr(value) for value in duplicates)}")
    decisions = sorted(
        (audit_record(record, audit_date, environment=environment) for record in records),
        key=lambda item: item["cafe_id"],
    )
    publishable = sum(1 for item in decisions if item["publishable"])
    return {
        "schema_version": "2.0",
        "as_of": audit_date,
        "environment": environment,
        "scope": {
            "name": "Greater Taipei",
            "city_aliases": {key: GREATER_TAIPEI_CITY_ALIASES[key] for key in sorted(GREATER_TAIPEI_CITY_ALIASES)},
            "geofence": GREATER_TAIPEI_GEOFENCE,
            "districts": {
                city: sorted(GREATER_TAIPEI_DISTRICTS[city])
                for city in sorted(GREATER_TAIPEI_DISTRICTS)
            },
        },
        "freshness_days": {field: FRESHNESS_DAYS[field] for field in sorted(FRESHNESS_DAYS)},
        "summary": {
            "total": len(decisions),
            "publishable": publishable,
            "blocked": len(decisions) - publishable,
        },
        "records": decisions,
    }
