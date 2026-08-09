#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import write_jsonl
from cafe_work_finder.normalize import normalize_manual_row
from cafe_work_finder.schema import validate_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize manually reviewed cafe CSV rows into JSONL.")
    parser.add_argument("--input", default="data/raw/manual_cafe_seed.csv")
    parser.add_argument("--output", default="data/processed/manual_cafes.normalized.jsonl")
    parser.add_argument("--skip-invalid", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    records = []
    errors = []
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        for line_number, row in enumerate(csv.DictReader(handle), start=2):
            record = normalize_manual_row(row)
            try:
                validate_record(record)
            except ValueError as exc:
                if not args.skip_invalid:
                    errors.append(f"{input_path}:{line_number}: {exc}")
                    continue
            records.append(record)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    count = write_jsonl(output_path, records)
    print(f"Wrote {count} normalized manual records to {output_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

