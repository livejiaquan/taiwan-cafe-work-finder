from __future__ import annotations

import copy
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from cafe_work_finder.io import AtomicDurabilityError, read_jsonl, write_jsonl, write_text_atomic
from cafe_work_finder.normalize import (
    MANUAL_COLUMNS,
    normalize_google_place,
    normalize_manual_row,
    normalize_osm_element,
)
from cafe_work_finder.publication import audit_record, audit_records
from cafe_work_finder.schema import validate_record


ROOT = Path(__file__).resolve().parents[1]


def verified_manual_row(**overrides: str) -> dict[str, str]:
    row = {field: "" for field in MANUAL_COLUMNS}
    row.update(
        {
            "name": "Trust Cafe",
            "city": "臺北市",
            "district": "中山區",
            "address": "臺北市中山區測試路1號",
            "lat": "25.0521",
            "lng": "121.5211",
            "unlimited_time": "unknown",
            "outlets": "some",
            "wifi": "yes",
            "quietness": "quiet",
            "seat_comfort": "unknown",
            "meeting_suitability": "unknown",
            "solo_work_suitability": "high",
            "study_suitability": "unknown",
            "online_meeting_suitability": "unknown",
            "long_stay_suitability": "unknown",
            "food_available": "unknown",
            "reservation": "unknown",
            "source_url": "https://evidence.taiwan-cafe-work-finder.invalid/observations/trust-cafe",
            "source_title": "Trust Cafe direct observation",
            "source_type": "field_observation",
            "retrieved_at": "2026-08-01",
            "observed_at": "2026-08-01",
            "verification_method": "on_site_checklist",
            "policy_id": "project_field_observation_v1",
            "verified_at": "2026-08-01",
            "branch_identity_status": "resolved",
            "operational_status": "open",
            "rights_status": "cleared",
            "rights_basis": "Project-owned on-site observation",
            "attribution": "Taiwan Cafe Work Finder field observation",
            "confidence": "high",
        }
    )
    row.update(overrides)
    return row


class TrustFoundationTests(unittest.TestCase):
    def test_retrieval_does_not_manufacture_manual_verification(self):
        record = normalize_manual_row(
            verified_manual_row(observed_at="", verification_method="", verified_at="")
        )

        self.assertEqual(record["source_links"][0]["retrieved_at"], "2026-08-01")
        self.assertTrue(all(claim["observed_at"] == "" for claim in record["source_links"][0]["claims"]))
        self.assertEqual(record["last_verified_at"], "")
        validate_record(record)

    def test_osm_snapshot_time_is_provenance_not_observation(self):
        element = {
            "type": "node",
            "id": 123,
            "lat": 25.0,
            "lon": 121.5,
            "timestamp": "2026-05-30T08:00:00Z",
            "tags": {"amenity": "cafe", "name": "OSM Cafe", "internet_access": "wlan"},
        }

        record = normalize_osm_element(element, retrieved_at="2026-06-01")

        source = record["source_links"][0]
        self.assertEqual(source["retrieved_at"], "2026-06-01")
        self.assertEqual(source["source_updated_at"], "2026-05-30T08:00:00Z")
        self.assertTrue(all(claim["observed_at"] == "" for claim in source["claims"]))
        self.assertEqual(record["last_verified_at"], "")
        self.assertEqual(
            source["evidence_fields"],
            ["canonical_name", "coordinates", "work_attributes.wifi"],
        )
        self.assertNotIn("address", source["evidence_fields"])
        self.assertNotIn("work_attributes.opening_hours", source["evidence_fields"])
        validate_record(record)

    def test_osm_normalizer_derives_date_from_raw_snapshot_and_accepts_tmp_output(self):
        payload = {
            "_collection": {"retrieved_at": "2026-06-01"},
            "elements": [
                {
                    "type": "node",
                    "id": 123,
                    "lat": 25.0,
                    "lon": 121.5,
                    "tags": {"amenity": "cafe", "name": "OSM Cafe"},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "snapshot.json"
            output_path = Path(temp_dir) / "normalized.jsonl"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/normalize_osm.py"),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            record = read_jsonl(output_path)[0]
            self.assertEqual(record["source_links"][0]["retrieved_at"], "2026-06-01")
            self.assertEqual(record["last_verified_at"], "")

    def test_structural_validator_rejects_adversarial_types_and_metadata(self):
        valid = normalize_manual_row(verified_manual_row())
        mutations = []

        invalid_date = copy.deepcopy(valid)
        invalid_date["source_links"][0]["retrieved_at"] = "not-a-date"
        mutations.append(invalid_date)

        timezone_free_datetime = copy.deepcopy(valid)
        timezone_free_datetime["source_links"][0]["retrieved_at"] = "2026-08-01T10:00:00"
        mutations.append(timezone_free_datetime)

        missing_source_id = copy.deepcopy(valid)
        del missing_source_id["source_links"][0]["source_id"]
        mutations.append(missing_source_id)

        object_city = copy.deepcopy(valid)
        object_city["city"] = {"name": "臺北市"}
        mutations.append(object_city)

        javascript_contact = copy.deepcopy(valid)
        javascript_contact["contact"] = {"website_url": "javascript:alert(1)"}
        mutations.append(javascript_contact)

        boolean_coordinates = copy.deepcopy(valid)
        boolean_coordinates["coordinates"] = {"lat": True, "lng": 121.5}
        mutations.append(boolean_coordinates)

        unknown_evidence = copy.deepcopy(valid)
        unknown_evidence["source_links"][0]["evidence_fields"].append("wifi")
        mutations.append(unknown_evidence)

        for record in mutations:
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    validate_record(record)

    def test_structural_validator_rejects_unknown_closed_object_fields(self):
        valid = normalize_manual_row(verified_manual_row())
        mutations = []

        top_level = copy.deepcopy(valid)
        top_level["unexpected"] = True
        mutations.append(top_level)

        work_attributes = copy.deepcopy(valid)
        work_attributes["work_attributes"]["unexpected"] = "value"
        mutations.append(work_attributes)

        source = copy.deepcopy(valid)
        source["source_links"][0]["unexpected"] = "value"
        mutations.append(source)

        claim = copy.deepcopy(valid)
        claim["source_links"][0]["claims"][0]["unexpected"] = "value"
        mutations.append(claim)

        coordinates = copy.deepcopy(valid)
        coordinates["coordinates"]["accuracy"] = 5
        mutations.append(coordinates)

        external_id_value = copy.deepcopy(valid)
        external_id_value["external_ids"] = {"provider": 123}
        mutations.append(external_id_value)

        conflicted = next(
            record
            for record in read_jsonl(ROOT / "data/curated/cafes.seed.jsonl")
            if record["conflicts"]
        )
        conflict = copy.deepcopy(conflicted)
        conflict["conflicts"][0]["unexpected"] = "value"
        mutations.append(conflict)

        signal = copy.deepcopy(conflicted)
        signal["conflicts"][0]["signals"][0]["unexpected"] = "value"
        mutations.append(signal)

        for record in mutations:
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    validate_record(record)

    def test_json_schema_closes_canonical_objects_and_types_dynamic_maps(self):
        schema = json.loads((ROOT / "docs/cafe_record_schema.json").read_text(encoding="utf-8"))

        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["coordinates"]["anyOf"][0]["additionalProperties"])
        self.assertFalse(schema["properties"]["work_attributes"]["additionalProperties"])
        source = schema["properties"]["source_links"]["items"]
        self.assertFalse(source["additionalProperties"])
        self.assertFalse(source["properties"]["claims"]["items"]["additionalProperties"])
        conflict = schema["properties"]["conflicts"]["items"]
        self.assertFalse(conflict["additionalProperties"])
        self.assertFalse(conflict["properties"]["signals"]["items"]["additionalProperties"])
        self.assertEqual(schema["properties"]["external_ids"]["additionalProperties"]["type"], "string")
        self.assertIn("enum", schema["properties"]["field_confidence"]["propertyNames"])

    def test_provider_normalizers_reject_non_scalar_used_fields(self):
        valid_google = {
            "id": "google-1",
            "name": "places/google-1",
            "displayName": {"text": "Google Cafe"},
            "formattedAddress": "臺北市中山區測試路1號",
            "location": {"latitude": 25.05, "longitude": 121.52},
            "websiteUri": "https://google-cafe.example/",
            "googleMapsUri": "https://maps.google.com/?cid=google-1",
            "priceLevel": "PRICE_LEVEL_MODERATE",
            "regularOpeningHours": {"weekdayDescriptions": ["Monday: 09:00-18:00"]},
        }
        validate_record(normalize_google_place(valid_google, retrieved_at="2026-08-01"))

        google_mutations = []
        for field, value in [
            ("id", 123),
            ("name", ["places/google-1"]),
            ("formattedAddress", {"bad": 1}),
            ("websiteUri", 0),
            ("googleMapsUri", ["https://maps.google.com/"]),
            ("priceLevel", 2),
        ]:
            mutated = copy.deepcopy(valid_google)
            mutated[field] = value
            google_mutations.append((field, mutated))
        bad_display = copy.deepcopy(valid_google)
        bad_display["displayName"]["text"] = ["Bad"]
        google_mutations.append(("displayName.text", bad_display))
        bad_latitude = copy.deepcopy(valid_google)
        bad_latitude["location"]["latitude"] = "25.05"
        google_mutations.append(("location.latitude", bad_latitude))
        bad_longitude = copy.deepcopy(valid_google)
        bad_longitude["location"]["longitude"] = False
        google_mutations.append(("location.longitude", bad_longitude))
        bad_hours = copy.deepcopy(valid_google)
        bad_hours["regularOpeningHours"]["weekdayDescriptions"] = [123]
        google_mutations.append(("weekdayDescriptions", bad_hours))
        bad_types = copy.deepcopy(valid_google)
        bad_types["types"] = 42
        google_mutations.append(("types", bad_types))
        bad_rating = copy.deepcopy(valid_google)
        bad_rating["rating"] = "4.5"
        google_mutations.append(("rating", bad_rating))
        bad_rating_count = copy.deepcopy(valid_google)
        bad_rating_count["userRatingCount"] = "10"
        google_mutations.append(("userRatingCount", bad_rating_count))

        for field, place in google_mutations:
            with self.subTest(provider="google", field=field):
                with self.assertRaises((TypeError, ValueError)):
                    normalize_google_place(place, retrieved_at="2026-08-01")

        valid_osm = {
            "type": "node",
            "id": 1,
            "lat": 25.05,
            "lon": 121.52,
            "timestamp": "2026-08-01T00:00:00Z",
            "tags": {
                "amenity": "cafe",
                "name": "OSM Cafe",
                "addr:city": "臺北市",
                "phone": "+886-2-1234-5678",
            },
        }
        validate_record(normalize_osm_element(valid_osm, retrieved_at="2026-08-01"))

        osm_mutations = []
        for field, value in [
            ("type", "banana"),
            ("id", {"bad": 1}),
            ("lat", "25.05"),
            ("lon", False),
            ("timestamp", ""),
            ("timestamp", "not-a-date"),
            ("timestamp", ["2026-08-01"]),
        ]:
            mutated = copy.deepcopy(valid_osm)
            mutated[field] = value
            osm_mutations.append((field, mutated))
        for tag in [
            "amenity",
            "name",
            "name:zh",
            "name:en",
            "addr:city",
            "addr:district",
            "addr:suburb",
            "addr:street",
            "addr:housenumber",
            "website",
            "contact:website",
            "phone",
            "contact:phone",
            "internet_access",
            "opening_hours",
            "minimum_order",
            "unexpected",
        ]:
            mutated = copy.deepcopy(valid_osm)
            mutated["tags"][tag] = {"bad": 1}
            osm_mutations.append((f"tags.{tag}", mutated))

        for field, element in osm_mutations:
            with self.subTest(provider="osm", field=field):
                with self.assertRaises((TypeError, ValueError)):
                    normalize_osm_element(element, retrieved_at="2026-08-01")

    def test_evidence_fields_must_exactly_match_structured_claims(self):
        valid = normalize_manual_row(verified_manual_row())
        source = valid["source_links"][0]
        self.assertEqual(set(source["evidence_fields"]), {claim["field"] for claim in source["claims"]})

        missing_claim = copy.deepcopy(valid)
        missing_claim["source_links"][0]["claims"].pop()
        with self.assertRaises(ValueError):
            validate_record(missing_claim)

    def test_claim_value_must_match_canonical_value(self):
        record = normalize_manual_row(verified_manual_row())
        quietness_claim = next(
            claim
            for claim in record["source_links"][0]["claims"]
            if claim["field"] == "work_attributes.quietness"
        )
        quietness_claim["value"] = "noisy"

        decision = audit_record(record, "2026-08-09", environment="test")

        self.assertFalse(decision["publishable"])
        self.assertEqual(decision["field_status"]["work_attributes.quietness"]["status"], "value_mismatch")
        self.assertEqual(decision["status"], "conflicted")

    def test_stale_prior_value_does_not_conflict_with_fresh_matching_claim(self):
        record = normalize_manual_row(verified_manual_row())
        stale_source = copy.deepcopy(record["source_links"][0])
        stale_source["source_id"] = "source-stale-quietness"
        stale_source["url"] = "https://evidence.taiwan-cafe-work-finder.invalid/observations/stale-quietness"
        stale_source["retrieved_at"] = "2025-01-01"
        stale_claim = next(
            copy.deepcopy(claim)
            for claim in stale_source["claims"]
            if claim["field"] == "work_attributes.quietness"
        )
        stale_claim["value"] = "noisy"
        stale_claim["observed_at"] = "2025-01-01"
        stale_source["claims"] = [stale_claim]
        stale_source["evidence_fields"] = ["work_attributes.quietness"]
        record["source_links"].append(stale_source)

        decision = audit_record(record, "2026-08-09", environment="test")

        self.assertTrue(decision["publishable"], decision["blockers"])

        stale_claim["observed_at"] = "2026-08-02"
        mismatch = audit_record(record, "2026-08-09", environment="test")
        self.assertEqual(mismatch["field_status"]["work_attributes.quietness"]["status"], "value_mismatch")

    def test_every_known_negative_or_limiting_work_field_is_audited(self):
        record = normalize_manual_row(
            verified_manual_row(outlets="none", wifi="no", quietness="lively", solo_work_suitability="low")
        )
        decision = audit_record(record, "2026-08-09", environment="test")
        for field in [
            "work_attributes.outlets",
            "work_attributes.wifi",
            "work_attributes.quietness",
            "work_attributes.solo_work_suitability",
        ]:
            self.assertIn(field, decision["field_status"])
            self.assertEqual(decision["field_status"][field]["status"], "fresh")

        unsupported = copy.deepcopy(record)
        source = unsupported["source_links"][0]
        source["claims"] = [claim for claim in source["claims"] if claim["field"] != "work_attributes.outlets"]
        source["evidence_fields"].remove("work_attributes.outlets")
        unsupported["field_confidence"].pop("work_attributes.outlets")
        blocked = audit_record(unsupported, "2026-08-09", environment="test")
        self.assertEqual(blocked["field_status"]["work_attributes.outlets"]["status"], "unsupported")

    def test_invalid_manual_enum_does_not_create_claim_or_confidence(self):
        record = normalize_manual_row(verified_manual_row(wifi="definitely"))
        source = record["source_links"][0]

        self.assertEqual(record["work_attributes"]["wifi"], "unknown")
        self.assertNotIn("work_attributes.wifi", source["evidence_fields"])
        self.assertNotIn("work_attributes.wifi", {claim["field"] for claim in source["claims"]})
        self.assertNotIn("work_attributes.wifi", record["field_confidence"])

    def test_reviewed_policy_cannot_be_spoofed_by_free_text_metadata(self):
        forum_url_spoof = normalize_manual_row(
            verified_manual_row(source_url="https://www.dcard.tw/f/food/p/241838488")
        )
        with self.assertRaises(ValueError):
            validate_record(forum_url_spoof)

        arbitrary_basis = normalize_manual_row(verified_manual_row(rights_basis="assumed reusable"))
        with self.assertRaises(ValueError):
            validate_record(arbitrary_basis)

    def test_scope_rejects_tokyo_even_with_fresh_project_claims(self):
        record = normalize_manual_row(
            verified_manual_row(
                city="Tokyo",
                district="Shibuya",
                address="Tokyo Shibuya 1",
                lat="35.6762",
                lng="139.6503",
            )
        )

        decision = audit_record(record, "2026-08-09")

        codes = {blocker["code"] for blocker in decision["blockers"]}
        self.assertFalse(decision["publishable"])
        self.assertIn("outside_city_scope", codes)
        self.assertIn("outside_geofence", codes)

    def test_source_provenance_timestamps_after_as_of_are_blocked(self):
        for timestamp_field in ["retrieved_at", "published_at", "source_updated_at"]:
            with self.subTest(timestamp_field=timestamp_field):
                record = normalize_manual_row(verified_manual_row())
                record["source_links"][0][timestamp_field] = "2026-08-10"
                decision = audit_record(record, "2026-08-09")
                self.assertIn("source_timestamp_future", {item["code"] for item in decision["blockers"]})

    def test_future_claim_is_globally_blocked_even_when_another_claim_is_fresh(self):
        record = normalize_manual_row(verified_manual_row())
        future_source = copy.deepcopy(record["source_links"][0])
        future_source["source_id"] = "future-extra-source"
        future_source["url"] = "https://evidence.taiwan-cafe-work-finder.invalid/observations/future-extra"
        future_source["retrieved_at"] = "2026-08-10"
        future_claim = next(
            copy.deepcopy(claim)
            for claim in future_source["claims"]
            if claim["field"] == "canonical_name"
        )
        future_claim["observed_at"] = "2026-08-10"
        future_claim["value"] = "Future contradictory name"
        future_source["claims"] = [future_claim]
        future_source["evidence_fields"] = ["canonical_name"]
        record["source_links"].append(future_source)

        decision = audit_record(record, "2026-08-09", environment="test")

        codes = {item["code"] for item in decision["blockers"]}
        self.assertIn("claim_observation_future", codes)
        self.assertEqual(decision["field_status"]["canonical_name"]["status"], "fresh")

    def test_publication_supporting_chronology_is_fail_closed(self):
        base = normalize_manual_row(verified_manual_row())
        cases: dict[str, dict] = {}

        published_after_retrieval = copy.deepcopy(base)
        published_after_retrieval["source_links"][0]["published_at"] = "2026-08-02"
        cases["published_after_retrieval"] = published_after_retrieval

        updated_after_retrieval = copy.deepcopy(base)
        updated_after_retrieval["source_links"][0]["source_updated_at"] = "2026-08-02"
        cases["updated_after_retrieval"] = updated_after_retrieval

        observed_after_retrieval = copy.deepcopy(base)
        for claim in observed_after_retrieval["source_links"][0]["claims"]:
            claim["observed_at"] = "2026-08-02"
        observed_after_retrieval["last_verified_at"] = "2026-08-02"
        cases["observed_after_retrieval"] = observed_after_retrieval

        retrieval_after_verification = copy.deepcopy(base)
        retrieval_after_verification["source_links"][0]["retrieved_at"] = "2026-08-02"
        cases["retrieval_after_verification"] = retrieval_after_verification

        same_day_observed_after_retrieval = copy.deepcopy(base)
        same_day_observed_after_retrieval["source_links"][0]["retrieved_at"] = "2026-08-01T10:00:00+08:00"
        same_day_observed_after_retrieval["last_verified_at"] = "2026-08-01T12:00:00+08:00"
        for claim in same_day_observed_after_retrieval["source_links"][0]["claims"]:
            claim["observed_at"] = "2026-08-01T09:00:00+08:00"
        same_day_observed_after_retrieval["source_links"][0]["claims"][0]["observed_at"] = (
            "2026-08-01T11:00:00+08:00"
        )
        cases["same_day_observed_after_retrieval"] = same_day_observed_after_retrieval

        same_day_published_after_retrieval = copy.deepcopy(base)
        same_day_published_after_retrieval["source_links"][0]["retrieved_at"] = "2026-08-01T10:00:00+08:00"
        same_day_published_after_retrieval["source_links"][0]["published_at"] = "2026-08-01T11:00:00+08:00"
        same_day_published_after_retrieval["last_verified_at"] = "2026-08-01T12:00:00+08:00"
        for claim in same_day_published_after_retrieval["source_links"][0]["claims"]:
            claim["observed_at"] = "2026-08-01T09:00:00+08:00"
        cases["same_day_published_after_retrieval"] = same_day_published_after_retrieval

        same_day_retrieval_after_verification = copy.deepcopy(base)
        same_day_retrieval_after_verification["source_links"][0]["retrieved_at"] = "2026-08-01T12:00:00+08:00"
        same_day_retrieval_after_verification["last_verified_at"] = "2026-08-01T11:00:00+08:00"
        for claim in same_day_retrieval_after_verification["source_links"][0]["claims"]:
            claim["observed_at"] = "2026-08-01T09:00:00+08:00"
        cases["same_day_retrieval_after_verification"] = same_day_retrieval_after_verification

        offset_inversion = copy.deepcopy(base)
        offset_inversion["source_links"][0]["retrieved_at"] = "2026-08-01T11:00:00+08:00"
        offset_inversion["source_links"][0]["published_at"] = "2026-08-01T04:00:00Z"
        offset_inversion["last_verified_at"] = "2026-08-01T13:00:00+08:00"
        for claim in offset_inversion["source_links"][0]["claims"]:
            claim["observed_at"] = "2026-08-01T10:00:00+08:00"
        cases["different_offset_inversion"] = offset_inversion

        for label, record in cases.items():
            with self.subTest(label=label):
                decision = audit_record(record, "2026-08-09", environment="test")
                self.assertFalse(decision["publishable"])
                self.assertIn("source_chronology_invalid", {item["code"] for item in decision["blockers"]})

    def test_nonempty_public_optional_fields_require_matching_claims(self):
        for field, row_override in [
            ("branch_name", {"branch_name": "Main Branch"}),
            ("contact.website_url", {"website_url": "https://trust-cafe.example/"}),
            ("contact.instagram_url", {"instagram_url": "https://instagram.com/trust-cafe"}),
            ("contact.facebook_url", {"facebook_url": "https://facebook.com/trust-cafe"}),
            ("contact.threads_url", {"threads_url": "https://threads.net/@trust-cafe"}),
            ("contact.google_maps_url", {"google_maps_url": "https://maps.google.com/?q=trust-cafe"}),
            ("contact.phone", {"phone": "+886-2-1234-5678"}),
        ]:
            with self.subTest(field=field):
                record = normalize_manual_row(verified_manual_row(**row_override))
                source = record["source_links"][0]
                source["claims"] = [claim for claim in source["claims"] if claim["field"] != field]
                source["evidence_fields"].remove(field)
                record["field_confidence"].pop(field)
                validate_record(record)

                decision = audit_record(record, "2026-08-09", environment="test")

                self.assertFalse(decision["publishable"])
                self.assertEqual(decision["field_status"][field]["status"], "unsupported")

    def test_resolved_conflicts_remain_production_blocked(self):
        record = normalize_manual_row(verified_manual_row())
        conflict = json.loads((ROOT / "data/raw/cafe_conflicts.json").read_text(encoding="utf-8"))[0]["conflict"]
        conflict["status"] = "resolved"
        record["conflicts"] = [conflict]
        validate_record(record)

        decision = audit_record(record, "2026-08-09")

        self.assertIn(
            "resolved_conflict_provenance_unimplemented",
            {item["code"] for item in decision["blockers"]},
        )

    def test_taipei_city_with_non_taipei_district_is_out_of_scope(self):
        record = normalize_manual_row(verified_manual_row(district="Shibuya"))

        decision = audit_record(record, "2026-08-09", environment="test")

        self.assertFalse(decision["publishable"])
        self.assertIn("outside_district_scope", {item["code"] for item in decision["blockers"]})

    def test_five_senses_is_machine_readable_unresolved_conflict_not_asserted_closed(self):
        records = read_jsonl(ROOT / "data/curated/cafes.seed.jsonl")
        record = next(item for item in records if item["canonical_name"] == "5 Senses Café")

        self.assertEqual(record["operational_status"], "conflicted")
        self.assertEqual(len(record["conflicts"]), 1)
        self.assertEqual(record["conflicts"][0]["status"], "unresolved")
        self.assertEqual({signal["reported_value"] for signal in record["conflicts"][0]["signals"]}, {"closed"})
        decision = audit_record(record, "2026-08-09")
        self.assertEqual(decision["status"], "conflicted")

    def test_manual_template_header_matches_normalizer_columns(self):
        with (ROOT / "data/raw/manual_cafe_seed.template.csv").open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        self.assertEqual(header, MANUAL_COLUMNS)

    def test_verified_record_is_publishable_and_retrieval_only_is_not(self):
        record = normalize_manual_row(verified_manual_row())

        decision = audit_record(record, "2026-08-09", environment="test")
        self.assertTrue(decision["publishable"], decision["blockers"])

        production = audit_record(record, "2026-08-09")
        self.assertFalse(production["publishable"])
        self.assertEqual(production["environment"], "production")
        self.assertIn("evidence_policy_blocked", {item["code"] for item in production["blockers"]})

        retrieval_only = copy.deepcopy(record)
        for claim in retrieval_only["source_links"][0]["claims"]:
            claim["observed_at"] = ""
        retrieval_only["source_links"][0]["published_at"] = "2026-08-08"
        retrieval_only["source_links"][0]["retrieved_at"] = "2026-08-09"
        retrieval_only["last_verified_at"] = ""
        blocked = audit_record(retrieval_only, "2026-08-09", environment="test")
        self.assertFalse(blocked["publishable"])
        self.assertIn("evidence_unknown", {item["code"] for item in blocked["blockers"]})

    def test_stale_closed_ambiguous_conflicted_and_rights_unknown_are_blocked(self):
        base = normalize_manual_row(verified_manual_row())
        cases = {}

        stale = copy.deepcopy(base)
        for claim in stale["source_links"][0]["claims"]:
            claim["observed_at"] = "2025-01-01"
        stale["last_verified_at"] = "2025-01-01"
        cases["stale"] = stale

        closed = normalize_manual_row(verified_manual_row(operational_status="closed"))
        cases["closed"] = closed

        ambiguous = normalize_manual_row(verified_manual_row(branch_identity_status="ambiguous"))
        cases["ambiguous"] = ambiguous

        rights_unknown = copy.deepcopy(base)
        rights_unknown["source_links"][0]["rights_status"] = "unknown"
        rights_unknown["source_links"][0]["rights_basis"] = ""
        future = copy.deepcopy(base)
        for claim in future["source_links"][0]["claims"]:
            claim["observed_at"] = "2026-08-10"
        cases["future"] = future

        for label, record in cases.items():
            with self.subTest(label=label):
                self.assertFalse(audit_record(record, "2026-08-09")["publishable"])

        with self.assertRaises(ValueError):
            validate_record(rights_unknown)

    def test_low_confidence_and_unmodeled_conditional_time_limit_are_blocked(self):
        base = normalize_manual_row(verified_manual_row())

        low_source = copy.deepcopy(base)
        low_source["source_links"][0]["confidence"] = "low"
        self.assertFalse(audit_record(low_source, "2026-08-09", environment="test")["publishable"])

        low_field = copy.deepcopy(base)
        low_field["field_confidence"]["work_attributes.quietness"] = "unknown"
        self.assertFalse(audit_record(low_field, "2026-08-09", environment="test")["publishable"])

        low_claim = copy.deepcopy(base)
        next(
            claim
            for claim in low_claim["source_links"][0]["claims"]
            if claim["field"] == "work_attributes.quietness"
        )["confidence"] = "low"
        self.assertFalse(audit_record(low_claim, "2026-08-09", environment="test")["publishable"])

        conditional = normalize_manual_row(verified_manual_row(unlimited_time="conditional"))
        decision = audit_record(conditional, "2026-08-09", environment="test")
        self.assertFalse(decision["publishable"])
        self.assertIn("condition_not_modeled", {item["code"] for item in decision["blockers"]})

    def test_cleared_rights_require_a_nonempty_basis(self):
        record = normalize_manual_row(verified_manual_row(rights_basis=""))

        with self.assertRaises(ValueError):
            validate_record(record)

    def test_current_legacy_seed_has_zero_publishable_records(self):
        records = read_jsonl(ROOT / "data/curated/cafes.seed.jsonl")
        report = audit_records(records, "2026-08-09")

        self.assertEqual(report["summary"], {"total": 8, "publishable": 0, "blocked": 8})
        self.assertEqual(report["environment"], "production")

    def test_audit_and_validator_reject_dataset_duplicate_ids(self):
        record = normalize_manual_row(verified_manual_row())
        with self.assertRaisesRegex(ValueError, "duplicate cafe_id"):
            audit_records([record, copy.deepcopy(record)], "2026-08-09")

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "duplicate.jsonl"
            write_jsonl(input_path, [record, copy.deepcopy(record)])
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/validate_dataset.py"),
                    "--input",
                    str(input_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("duplicate cafe_id", completed.stderr)

    def test_default_merge_does_not_promote_osm_discovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "curated.jsonl"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/merge_curated.py"),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            records = read_jsonl(output_path)
            self.assertEqual(len(records), 8)
            self.assertTrue(all(record["cafe_id"].startswith("manual-") for record in records))

    def test_merge_failures_do_not_replace_existing_output(self):
        record = normalize_manual_row(verified_manual_row())
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "curated.jsonl"
            output_path.write_text("sentinel\n", encoding="utf-8")

            missing = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/merge_curated.py"),
                    "--inputs",
                    str(temp_path / "missing.jsonl"),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(missing.returncode, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            empty_path = temp_path / "empty.jsonl"
            empty_path.write_text("", encoding="utf-8")
            empty = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/merge_curated.py"),
                    "--inputs",
                    str(empty_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(empty.returncode, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            duplicate_path = temp_path / "duplicate.jsonl"
            write_jsonl(duplicate_path, [record, copy.deepcopy(record)])
            duplicate = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/merge_curated.py"),
                    "--inputs",
                    str(duplicate_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("Duplicate cafe_id", duplicate.stderr)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

    def test_validate_dataset_missing_and_empty_absolute_inputs_fail_clearly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for input_path in [temp_path / "missing.jsonl", temp_path / "empty.jsonl"]:
                if input_path.name == "empty.jsonl":
                    input_path.write_text("", encoding="utf-8")
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/normalize/validate_dataset.py"),
                        "--input",
                        str(input_path),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(str(input_path), completed.stderr)

    def test_publication_audit_requires_explicit_as_of(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/quality/audit_publication_readiness.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--as-of", completed.stderr)

    def test_audit_cli_is_production_only_atomic_and_preserves_errors(self):
        record = normalize_manual_row(verified_manual_row())
        with self.assertRaisesRegex(ValueError, "environment"):
            audit_records([], "2026-08-09", environment="staging")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "audit.json"
            output_path.write_text("sentinel\n", encoding="utf-8")
            output_path.chmod(0o640)

            empty_path = temp_path / "empty.jsonl"
            empty_path.write_text("", encoding="utf-8")
            empty = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/quality/audit_publication_readiness.py"),
                    "--input",
                    str(empty_path),
                    "--as-of",
                    "2026-08-09",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(empty.returncode, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            duplicate_path = temp_path / "duplicate.jsonl"
            write_jsonl(duplicate_path, [record, copy.deepcopy(record)])
            duplicate = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/quality/audit_publication_readiness.py"),
                    "--input",
                    str(duplicate_path),
                    "--as-of",
                    "2026-08-09",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            malformed_path = temp_path / "malformed.jsonl"
            malformed_path.write_text("{not json\n", encoding="utf-8")
            malformed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/quality/audit_publication_readiness.py"),
                    "--input",
                    str(malformed_path),
                    "--as-of",
                    "2026-08-09",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(malformed.returncode, 0)
            self.assertNotIn("Traceback", malformed.stderr)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            invalid_as_of = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/quality/audit_publication_readiness.py"),
                    "--input",
                    str(duplicate_path),
                    "--as-of",
                    "not-a-date",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(invalid_as_of.returncode, 0)
            self.assertNotIn("Traceback", invalid_as_of.stderr)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            valid_path = temp_path / "valid.jsonl"
            write_jsonl(valid_path, [record])
            success = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/quality/audit_publication_readiness.py"),
                    "--input",
                    str(valid_path),
                    "--as-of",
                    "2026-08-09",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["environment"], "production")
            self.assertEqual(stat.S_IMODE(output_path.stat().st_mode), 0o640)

    def test_atomic_jsonl_write_preserves_old_file_on_generation_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "atomic.jsonl"
            output_path.write_text("sentinel\n", encoding="utf-8")

            def broken_records():
                yield {"first": True}
                raise RuntimeError("boom")

            with self.assertRaises(RuntimeError):
                write_jsonl(output_path, broken_records())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

    def test_atomic_writers_preserve_mode_and_fsync_file_and_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            text_path = Path(temp_dir) / "atomic.txt"
            text_path.write_text("old\n", encoding="utf-8")
            text_path.chmod(0o640)
            with mock.patch("cafe_work_finder.io.os.fsync") as fsync:
                write_text_atomic(text_path, "new\n")
            self.assertEqual(fsync.call_count, 2)
            self.assertEqual(stat.S_IMODE(text_path.stat().st_mode), 0o640)

            jsonl_path = Path(temp_dir) / "atomic.jsonl"
            jsonl_path.write_text("old\n", encoding="utf-8")
            jsonl_path.chmod(0o604)
            with mock.patch("cafe_work_finder.io.os.fsync") as fsync:
                write_jsonl(jsonl_path, [{"ok": True}])
            self.assertEqual(fsync.call_count, 2)
            self.assertEqual(stat.S_IMODE(jsonl_path.stat().st_mode), 0o604)

            with mock.patch(
                "cafe_work_finder.io.fsync_parent_directory",
                side_effect=OSError("simulated directory sync failure"),
            ):
                with self.assertRaisesRegex(
                    AtomicDurabilityError,
                    "target replaced; directory durability uncertain",
                ):
                    write_text_atomic(text_path, "committed-but-unsynced\n")
            self.assertEqual(text_path.read_text(encoding="utf-8"), "committed-but-unsynced\n")

    def test_all_normalizers_reject_zero_or_malformed_input_without_replacing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            conflicts_path = temp_path / "conflicts.json"
            conflicts_path.write_text("[]\n", encoding="utf-8")
            manual_path = temp_path / "header-only.csv"
            with manual_path.open("w", encoding="utf-8", newline="") as handle:
                csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS).writeheader()

            cases = [
                (
                    "manual_header_only",
                    ROOT / "scripts/normalize/normalize_manual.py",
                    ["--input", str(manual_path), "--conflicts", str(conflicts_path)],
                ),
            ]
            zero_byte_manual_path = temp_path / "zero-byte.csv"
            zero_byte_manual_path.write_bytes(b"")
            cases.append(
                (
                    "manual_zero_byte",
                    ROOT / "scripts/normalize/normalize_manual.py",
                    ["--input", str(zero_byte_manual_path), "--conflicts", str(conflicts_path)],
                )
            )
            valid_manual_path = temp_path / "valid-manual.csv"
            with valid_manual_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS)
                writer.writeheader()
                writer.writerow(verified_manual_row())
            malformed_conflicts_path = temp_path / "malformed-conflicts.json"
            malformed_conflicts_path.write_text("{not json", encoding="utf-8")
            cases.append(
                (
                    "manual_malformed_conflicts",
                    ROOT / "scripts/normalize/normalize_manual.py",
                    ["--input", str(valid_manual_path), "--conflicts", str(malformed_conflicts_path)],
                )
            )
            for source_name, script_name, payload in [
                ("osm_empty", "normalize_osm.py", {"_collection": {"retrieved_at": "2026-08-01"}, "elements": []}),
                (
                    "osm_invalid_collection",
                    "normalize_osm.py",
                    {"_collection": [], "elements": []},
                ),
                (
                    "osm_non_cafe",
                    "normalize_osm.py",
                    {
                        "_collection": {"retrieved_at": "2026-08-01"},
                        "elements": [{"type": "node", "id": 1, "lat": 25.0, "lon": 121.5, "tags": {"amenity": "restaurant"}}],
                    },
                ),
                (
                    "osm_mixed_invalid",
                    "normalize_osm.py",
                    {
                        "_collection": {"retrieved_at": "2026-08-01"},
                        "elements": [
                            {"type": "node", "id": 1, "lat": 25.0, "lon": 121.5, "tags": {"amenity": "cafe", "name": "Valid"}},
                            {"type": "node", "id": 2, "lat": 25.0, "lon": 121.5, "tags": []},
                        ],
                    },
                ),
                (
                    "osm_mixed_bad_scalar",
                    "normalize_osm.py",
                    {
                        "_collection": {"retrieved_at": "2026-08-01"},
                        "elements": [
                            {"type": "node", "id": 1, "lat": 25.0, "lon": 121.5, "tags": {"amenity": "cafe", "name": "Valid"}},
                            {"type": "node", "id": 2, "lat": 25.0, "lon": 121.5, "timestamp": "bad", "tags": {"amenity": "cafe", "name": {"bad": 1}}},
                        ],
                    },
                ),
                ("google_empty", "normalize_google_places.py", {"_collection": {"retrieved_at": "2026-08-01"}, "places": []}),
                (
                    "google_invalid_collection",
                    "normalize_google_places.py",
                    {"_collection": [], "places": []},
                ),
                (
                    "google_mixed_invalid",
                    "normalize_google_places.py",
                    {
                        "_collection": {"retrieved_at": "2026-08-01"},
                        "places": [
                            {"id": "valid", "displayName": {"text": "Valid"}},
                            {"id": "invalid", "displayName": []},
                        ],
                    },
                ),
                (
                    "google_mixed_bad_scalar",
                    "normalize_google_places.py",
                    {
                        "_collection": {"retrieved_at": "2026-08-01"},
                        "places": [
                            {"id": "valid", "displayName": {"text": "Valid"}},
                            {"id": "invalid", "displayName": {"text": "Invalid"}, "formattedAddress": {"bad": 1}},
                        ],
                    },
                ),
            ]:
                input_path = temp_path / f"{source_name}.json"
                input_path.write_text(json.dumps(payload), encoding="utf-8")
                cases.append(
                    (
                        source_name,
                        ROOT / "scripts/normalize" / script_name,
                        ["--input", str(input_path)],
                    )
                )
            for source_name, script_name in [
                ("osm_malformed", "normalize_osm.py"),
                ("google_malformed", "normalize_google_places.py"),
            ]:
                input_path = temp_path / f"{source_name}.json"
                input_path.write_text("{not json", encoding="utf-8")
                cases.append(
                    (
                        source_name,
                        ROOT / "scripts/normalize" / script_name,
                        ["--input", str(input_path)],
                    )
                )

            for label, script_path, arguments in cases:
                with self.subTest(label=label):
                    output_path = temp_path / f"{label}.jsonl"
                    output_path.write_text("sentinel\n", encoding="utf-8")
                    output_path.chmod(0o640)
                    completed = subprocess.run(
                        [sys.executable, str(script_path), *arguments, "--output", str(output_path)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")
                    self.assertEqual(stat.S_IMODE(output_path.stat().st_mode), 0o640)
                    self.assertEqual(list(temp_path.glob(f".{output_path.name}.*.tmp")), [])
                    self.assertTrue(completed.stderr.strip())
                    self.assertNotIn("Traceback", completed.stderr)

            skip_all_path = temp_path / "skip-all.csv"
            invalid = verified_manual_row(source_url="javascript:invalid")
            with skip_all_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS)
                writer.writeheader()
                writer.writerow(invalid)
            skip_output = temp_path / "skip-all.jsonl"
            skip_output.write_text("sentinel\n", encoding="utf-8")
            skip_all = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/normalize_manual.py"),
                    "--input",
                    str(skip_all_path),
                    "--conflicts",
                    str(conflicts_path),
                    "--output",
                    str(skip_output),
                    "--skip-invalid",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(skip_all.returncode, 0)
            self.assertEqual(skip_output.read_text(encoding="utf-8"), "sentinel\n")

    def test_source_normalizers_reject_duplicate_cafe_ids_without_replacing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            conflicts_path = temp_path / "conflicts.json"
            conflicts_path.write_text("[]\n", encoding="utf-8")

            manual_path = temp_path / "manual.csv"
            with manual_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS)
                writer.writeheader()
                writer.writerows([verified_manual_row(), verified_manual_row()])

            osm_element = {
                "type": "node",
                "id": 1,
                "lat": 25.05,
                "lon": 121.52,
                "timestamp": "2026-08-01T00:00:00Z",
                "tags": {"amenity": "cafe", "name": "Duplicate OSM Cafe"},
            }
            osm_path = temp_path / "osm.json"
            osm_path.write_text(
                json.dumps(
                    {
                        "_collection": {"retrieved_at": "2026-08-01"},
                        "elements": [osm_element, copy.deepcopy(osm_element)],
                    }
                ),
                encoding="utf-8",
            )

            google_place = {
                "id": "duplicate-google-id",
                "displayName": {"text": "Duplicate Google Cafe"},
                "googleMapsUri": "https://maps.google.com/?cid=duplicate-google-id",
            }
            google_path = temp_path / "google.json"
            google_path.write_text(
                json.dumps(
                    {
                        "_collection": {"retrieved_at": "2026-08-01"},
                        "places": [google_place, copy.deepcopy(google_place)],
                    }
                ),
                encoding="utf-8",
            )

            cases = [
                (
                    "manual",
                    ROOT / "scripts/normalize/normalize_manual.py",
                    ["--input", str(manual_path), "--conflicts", str(conflicts_path)],
                ),
                (
                    "osm",
                    ROOT / "scripts/normalize/normalize_osm.py",
                    ["--input", str(osm_path)],
                ),
                (
                    "google",
                    ROOT / "scripts/normalize/normalize_google_places.py",
                    ["--input", str(google_path)],
                ),
            ]
            for label, script_path, arguments in cases:
                with self.subTest(label=label):
                    output_path = temp_path / f"{label}.normalized.jsonl"
                    output_path.write_text("sentinel\n", encoding="utf-8")
                    completed = subprocess.run(
                        [sys.executable, str(script_path), *arguments, "--output", str(output_path)],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn("duplicate cafe_id", completed.stderr)
                    self.assertNotIn("Traceback", completed.stderr)
                    self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

    def test_conflict_registry_requires_exactly_one_raw_match(self):
        registry_entry = json.loads(
            (ROOT / "data/raw/cafe_conflicts.json").read_text(encoding="utf-8")
        )[0]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "manual.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS)
                writer.writeheader()
                writer.writerow(verified_manual_row())
            output_path = temp_path / "normalized.jsonl"
            output_path.write_text("sentinel\n", encoding="utf-8")

            orphan_path = temp_path / "orphan.json"
            orphan_path.write_text(json.dumps([registry_entry]), encoding="utf-8")
            orphan = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/normalize_manual.py"),
                    "--input",
                    str(input_path),
                    "--conflicts",
                    str(orphan_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(orphan.returncode, 0)
            self.assertIn("orphan", orphan.stderr.lower())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            matched_entry = copy.deepcopy(registry_entry)
            matched_entry["match"] = {
                "canonical_name": "Trust Cafe",
                "source_url": verified_manual_row()["source_url"],
            }
            duplicate_path = temp_path / "duplicate-conflicts.json"
            duplicate_path.write_text(json.dumps([matched_entry, copy.deepcopy(matched_entry)]), encoding="utf-8")
            duplicate = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/normalize_manual.py"),
                    "--input",
                    str(input_path),
                    "--conflicts",
                    str(duplicate_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn("more than once", duplicate.stderr)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

            single_match_path = temp_path / "single-match.json"
            single_match_path.write_text(json.dumps([matched_entry]), encoding="utf-8")
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS)
                writer.writeheader()
                writer.writerows([verified_manual_row(), verified_manual_row()])
            ambiguous = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/normalize_manual.py"),
                    "--input",
                    str(input_path),
                    "--conflicts",
                    str(single_match_path),
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(ambiguous.returncode, 0)
            self.assertIn("ambiguous", ambiguous.stderr.lower())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")

    def test_collectors_never_replace_raw_output_on_empty_or_disabled_live_collection(self):
        spec = importlib.util.spec_from_file_location(
            "collect_overpass_for_test",
            ROOT / "scripts/collectors/collect_overpass.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        overpass = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(overpass)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            raw_path = temp_path / "overpass.json"
            query_path = temp_path / "query.overpassql"
            complete_element = {
                "type": "node",
                "id": 1,
                "lat": 25.05,
                "lon": 121.52,
                "timestamp": "2026-08-01T00:00:00Z",
                "tags": {"amenity": "cafe", "name": "Collected Cafe"},
            }
            for response in [
                {"elements": []},
                {"unexpected": True},
                {"remark": "runtime timeout", "elements": [complete_element]},
                {"error": "runtime error", "elements": [complete_element]},
                {"elements": [42]},
                {"elements": [{"type": "node", "id": 1, "lat": 25.05, "lon": 121.52, "tags": {"amenity": "cafe"}}]},
                {
                    "elements": [
                        {
                            **complete_element,
                            "timestamp": "not-a-date",
                        }
                    ]
                },
                {"elements": [complete_element, copy.deepcopy(complete_element)]},
                RuntimeError("network down"),
            ]:
                with self.subTest(response=repr(response)):
                    raw_path.write_text("sentinel\n", encoding="utf-8")
                    replacement = mock.Mock(side_effect=response) if isinstance(response, Exception) else mock.Mock(return_value=response)
                    with mock.patch.object(overpass, "fetch_overpass", replacement), mock.patch.object(
                        sys,
                        "argv",
                        [
                            "collect_overpass.py",
                            "--output",
                            str(raw_path),
                            "--query-output",
                            str(query_path),
                        ],
                    ):
                        self.assertNotEqual(overpass.main(), 0)
                    self.assertEqual(raw_path.read_text(encoding="utf-8"), "sentinel\n")

            raw_path.write_text("sentinel\n", encoding="utf-8")
            raw_path.chmod(0o640)
            with mock.patch.object(overpass, "fetch_overpass", return_value={"elements": [complete_element]}), mock.patch.object(
                sys,
                "argv",
                [
                    "collect_overpass.py",
                    "--output",
                    str(raw_path),
                    "--query-output",
                    str(query_path),
                ],
            ):
                self.assertEqual(overpass.main(), 0)
            collected = json.loads(raw_path.read_text(encoding="utf-8"))
            self.assertEqual(len(collected["elements"]), 1)
            self.assertIn("retrieved_at", collected["_collection"])
            self.assertEqual(stat.S_IMODE(raw_path.stat().st_mode), 0o640)

            durability_stderr = io.StringIO()
            with mock.patch.object(overpass, "fetch_overpass", return_value={"elements": [complete_element]}), mock.patch.object(
                overpass,
                "write_text_atomic",
                side_effect=[None, AtomicDurabilityError(raw_path, OSError("directory sync failed"))],
            ), mock.patch.object(
                sys,
                "argv",
                [
                    "collect_overpass.py",
                    "--output",
                    str(raw_path),
                    "--query-output",
                    str(query_path),
                ],
            ), contextlib.redirect_stderr(durability_stderr):
                self.assertNotEqual(overpass.main(), 0)
            self.assertIn("target replaced; directory durability uncertain", durability_stderr.getvalue())
            self.assertNotIn("raw output was not replaced", durability_stderr.getvalue())

            google_path = temp_path / "google.json"
            google_path.write_text("sentinel\n", encoding="utf-8")
            disabled = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/collectors/collect_google_places.py"),
                    "--output",
                    str(google_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(disabled.returncode, 0)
            self.assertEqual(google_path.read_text(encoding="utf-8"), "sentinel\n")

    def test_skip_invalid_does_not_append_invalid_manual_row(self):
        valid = verified_manual_row()
        invalid = verified_manual_row(name="Invalid Cafe", source_url="javascript:bad")
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "manual.csv"
            output_path = Path(temp_dir) / "normalized.jsonl"
            conflicts_path = Path(temp_dir) / "conflicts.json"
            conflicts_path.write_text("[]\n", encoding="utf-8")
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MANUAL_COLUMNS)
                writer.writeheader()
                writer.writerows([valid, invalid])
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/normalize/normalize_manual.py"),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--conflicts",
                    str(conflicts_path),
                    "--skip-invalid",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(len(read_jsonl(output_path)), 1)
            self.assertIn("Skipping", completed.stderr)


if __name__ == "__main__":
    unittest.main()
