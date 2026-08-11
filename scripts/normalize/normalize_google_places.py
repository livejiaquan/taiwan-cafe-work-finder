#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import AtomicDurabilityError, display_path, write_jsonl
from cafe_work_finder.normalize import normalize_google_place
from cafe_work_finder.schema import is_iso_date_or_datetime, validate_record, validate_unique_cafe_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Google Places Text Search JSON into canonical JSONL.")
    parser.add_argument("--input", default="data/raw/google_places_taipei_sample.json")
    parser.add_argument("--output", default="data/processed/google_places.normalized.jsonl")
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
        print(f"Invalid Google Places JSON {display_path(input_path, ROOT)}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print(f"Invalid Google Places JSON {display_path(input_path, ROOT)}: root must be an object", file=sys.stderr)
        return 1
    collection = payload.get("_collection", {})
    if not isinstance(collection, dict):
        print("Invalid Google Places JSON: _collection must be an object", file=sys.stderr)
        return 1
    retrieved_at = args.retrieved_at or collection.get("retrieved_at")
    if not retrieved_at:
        print(
            "Snapshot retrieval date is missing; provide raw _collection.retrieved_at or --retrieved-at.",
            file=sys.stderr,
        )
        return 2
    if not isinstance(retrieved_at, str) or not is_iso_date_or_datetime(retrieved_at):
        print(
            "Invalid Google Places JSON: retrieved_at must be an ISO 8601 date or timezone-aware datetime",
            file=sys.stderr,
        )
        return 1
    places = payload.get("places", [])
    if not isinstance(places, list):
        print("Invalid Google Places JSON: places must be a list", file=sys.stderr)
        return 1
    records = []
    errors = []
    for index, place in enumerate(places):
        if not isinstance(place, dict):
            errors.append(f"places[{index}] must be an object")
            continue
        try:
            record = normalize_google_place(place, retrieved_at=retrieved_at)
            validate_record(record)
        except (TypeError, ValueError) as exc:
            errors.append(f"places[{index}]: {exc}")
            continue
        records.append(record)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("Google Places normalization failed; output was not replaced", file=sys.stderr)
        return 1
    if not records:
        print("Google Places normalization failed: zero place records; output was not replaced", file=sys.stderr)
        return 1
    try:
        validate_unique_cafe_ids(records, "Google Places normalization")
    except ValueError as exc:
        print(f"Google Places normalization failed: {exc}; output was not replaced", file=sys.stderr)
        return 1

    try:
        count = write_jsonl(output_path, records)
    except AtomicDurabilityError as exc:
        print(f"Google Places output durability failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Google Places output failed before replacement: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {count} normalized Google Places records to {display_path(output_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
