#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import AtomicDurabilityError, display_path, read_jsonl, write_jsonl
from cafe_work_finder.schema import validate_record


DEFAULT_INPUTS = [
    "data/processed/manual_cafes.normalized.jsonl",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge normalized records into a curated seed JSONL file.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=DEFAULT_INPUTS,
        help="Explicit normalized inputs. Default is reviewed manual candidates only; discovery feeds require opt-in.",
    )
    parser.add_argument("--output", default="data/curated/cafes.seed.jsonl")
    parser.add_argument("--manual-only", action="store_true", help="Only merge the manual seed dataset.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_paths = [ROOT / path for path in args.inputs]
    if args.manual_only:
        input_paths = [ROOT / "data/processed/manual_cafes.normalized.jsonl"]

    errors: list[str] = []
    merged: dict[str, dict] = {}
    origins: dict[str, str] = {}
    for path in input_paths:
        if not path.exists():
            errors.append(f"Input not found: {display_path(path, ROOT)}")
            continue
        try:
            input_records = read_jsonl(path)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        if not input_records:
            errors.append(f"Input is empty: {display_path(path, ROOT)}")
            continue
        for line_number, record in enumerate(input_records, start=1):
            try:
                validate_record(record)
            except ValueError as exc:
                errors.append(f"{display_path(path, ROOT)}:{line_number}: {exc}")
                continue
            cafe_id = record["cafe_id"]
            if cafe_id in merged:
                errors.append(
                    f"Duplicate cafe_id {cafe_id!r}: {origins[cafe_id]} and "
                    f"{display_path(path, ROOT)}:{line_number}"
                )
                continue
            merged[cafe_id] = record
            origins[cafe_id] = f"{display_path(path, ROOT)}:{line_number}"

    if not merged and not errors:
        errors.append("Merge result is empty")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Merge failed: {len(errors)} error(s); output was not replaced", file=sys.stderr)
        return 1

    records = sorted(merged.values(), key=lambda item: (item.get("city", ""), item.get("canonical_name", "")))
    if not records:
        print("Merge failed: result is empty; output was not replaced", file=sys.stderr)
        return 1
    output_path = ROOT / args.output
    try:
        count = write_jsonl(output_path, records)
    except AtomicDurabilityError as exc:
        print(f"Curated output durability failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Curated output failed before replacement: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {count} curated records to {display_path(output_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
