#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import display_path, read_jsonl
from cafe_work_finder.schema import validate_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate canonical cafe JSONL records.")
    parser.add_argument("--input", default="data/curated/cafes.seed.jsonl")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = ROOT / args.input
    if not path.exists():
        print(f"Input not found: {display_path(path, ROOT)}", file=sys.stderr)
        return 2
    errors = []
    seen_ids: dict[str, int] = {}
    try:
        records = read_jsonl(path)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not records:
        print(f"Validation failed: input is empty: {display_path(path, ROOT)}", file=sys.stderr)
        return 2
    for index, record in enumerate(records, start=1):
        try:
            validate_record(record)
        except ValueError as exc:
            errors.append(f"{display_path(path, ROOT)}:{index}: {exc}")
            continue
        cafe_id = record["cafe_id"]
        if cafe_id in seen_ids:
            errors.append(
                f"{display_path(path, ROOT)}:{index}: duplicate cafe_id {cafe_id!r}; "
                f"first seen at line {seen_ids[cafe_id]}"
            )
        else:
            seen_ids[cafe_id] = index

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed: {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(f"Validation passed: {len(records)} record(s) in {display_path(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
