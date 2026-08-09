#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import write_jsonl
from cafe_work_finder.normalize import normalize_google_place
from cafe_work_finder.schema import today_iso, validate_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Google Places Text Search JSON into canonical JSONL.")
    parser.add_argument("--input", default="data/raw/google_places_taipei_sample.json")
    parser.add_argument("--output", default="data/processed/google_places.normalized.jsonl")
    parser.add_argument("--retrieved-at", default=today_iso())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    if not input_path.exists():
        print(f"Input not found: {input_path.relative_to(ROOT)}", file=sys.stderr)
        return 2

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    places = payload.get("places", [])
    records = []
    for place in places:
        record = normalize_google_place(place, retrieved_at=args.retrieved_at)
        validate_record(record)
        records.append(record)

    count = write_jsonl(output_path, records)
    print(f"Wrote {count} normalized Google Places records to {output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

