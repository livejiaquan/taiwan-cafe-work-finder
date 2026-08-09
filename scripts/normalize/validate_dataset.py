#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import read_jsonl
from cafe_work_finder.schema import validate_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate canonical cafe JSONL records.")
    parser.add_argument("--input", default="data/curated/cafes.seed.jsonl")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = ROOT / args.input
    errors = []
    records = read_jsonl(path)
    for index, record in enumerate(records, start=1):
        try:
            validate_record(record)
        except ValueError as exc:
            errors.append(f"{path.relative_to(ROOT)}:{index}: {exc}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed: {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(f"Validation passed: {len(records)} record(s) in {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

