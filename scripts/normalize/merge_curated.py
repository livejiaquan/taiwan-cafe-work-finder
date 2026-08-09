#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import read_jsonl, write_jsonl
from cafe_work_finder.schema import validate_record


DEFAULT_INPUTS = [
    "data/processed/manual_cafes.normalized.jsonl",
    "data/processed/osm_cafes.normalized.jsonl",
    "data/processed/google_places.normalized.jsonl",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge normalized records into a curated seed JSONL file.")
    parser.add_argument("--inputs", nargs="*", default=DEFAULT_INPUTS)
    parser.add_argument("--output", default="data/curated/cafes.seed.jsonl")
    parser.add_argument("--manual-only", action="store_true", help="Only merge the manual seed dataset.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_paths = [ROOT / path for path in args.inputs]
    if args.manual_only:
        input_paths = [ROOT / "data/processed/manual_cafes.normalized.jsonl"]

    merged = {}
    for path in input_paths:
        if not path.exists():
            print(f"Skipping missing input: {path.relative_to(ROOT)}")
            continue
        for record in read_jsonl(path):
            validate_record(record)
            merged.setdefault(record["cafe_id"], record)

    records = sorted(merged.values(), key=lambda item: (item.get("city", ""), item.get("canonical_name", "")))
    count = write_jsonl(ROOT / args.output, records)
    print(f"Wrote {count} curated records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

