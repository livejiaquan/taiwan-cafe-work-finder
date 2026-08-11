#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import AtomicDurabilityError, display_path, write_jsonl
from cafe_work_finder.normalize import normalize_osm_element
from cafe_work_finder.schema import is_iso_date_or_datetime, validate_record, validate_unique_cafe_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Overpass cafe JSON into canonical JSONL.")
    parser.add_argument("--input", default="data/raw/overpass_taipei_sample.json")
    parser.add_argument("--output", default="data/processed/osm_cafes.normalized.jsonl")
    parser.add_argument(
        "--retrieved-at",
        help="Explicit snapshot retrieval date override. Defaults to raw _collection.retrieved_at.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    if not input_path.exists():
        print(f"Input not found: {display_path(input_path, ROOT)}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError, OSError) as exc:
        print(f"Invalid OSM JSON {display_path(input_path, ROOT)}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print(f"Invalid OSM JSON {display_path(input_path, ROOT)}: root must be an object", file=sys.stderr)
        return 1
    collection = payload.get("_collection", {})
    if not isinstance(collection, dict):
        print("Invalid OSM JSON: _collection must be an object", file=sys.stderr)
        return 1
    retrieved_at = args.retrieved_at or collection.get("retrieved_at")
    if not retrieved_at:
        print(
            "Snapshot retrieval date is missing; provide raw _collection.retrieved_at or --retrieved-at.",
            file=sys.stderr,
        )
        return 2
    if not isinstance(retrieved_at, str) or not is_iso_date_or_datetime(retrieved_at):
        print("Invalid OSM JSON: retrieved_at must be an ISO 8601 date or timezone-aware datetime", file=sys.stderr)
        return 1
    elements = payload.get("elements", [])
    if not isinstance(elements, list):
        print("Invalid OSM JSON: elements must be a list", file=sys.stderr)
        return 1
    records = []
    errors = []
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            errors.append(f"elements[{index}] must be an object")
            continue
        if "tags" not in element:
            errors.append(f"elements[{index}].tags is required")
            continue
        tags = element["tags"]
        if not isinstance(tags, dict):
            errors.append(f"elements[{index}].tags must be an object")
            continue
        if tags.get("amenity") != "cafe":
            errors.append(f"elements[{index}].tags.amenity must be 'cafe'")
            continue
        try:
            record = normalize_osm_element(element, retrieved_at=retrieved_at)
            validate_record(record)
        except (TypeError, ValueError) as exc:
            errors.append(f"elements[{index}]: {exc}")
            continue
        records.append(record)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("OSM normalization failed; output was not replaced", file=sys.stderr)
        return 1
    if not records:
        print("OSM normalization failed: zero cafe records; output was not replaced", file=sys.stderr)
        return 1
    try:
        validate_unique_cafe_ids(records, "OSM normalization")
    except ValueError as exc:
        print(f"OSM normalization failed: {exc}; output was not replaced", file=sys.stderr)
        return 1

    try:
        count = write_jsonl(output_path, records)
    except AtomicDurabilityError as exc:
        print(f"OSM output durability failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"OSM output failed before replacement: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {count} normalized OSM records to {display_path(output_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
