#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import AtomicDurabilityError, display_path, write_jsonl
from cafe_work_finder.normalize import normalize_manual_row
from cafe_work_finder.schema import validate_conflict_registry, validate_record, validate_unique_cafe_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize manually reviewed cafe CSV rows into JSONL.")
    parser.add_argument("--input", default="data/raw/manual_cafe_seed.csv")
    parser.add_argument("--output", default="data/processed/manual_cafes.normalized.jsonl")
    parser.add_argument("--conflicts", default="data/raw/cafe_conflicts.json")
    parser.add_argument("--skip-invalid", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    conflicts_path = ROOT / args.conflicts
    if not input_path.exists():
        print(f"Input not found: {display_path(input_path, ROOT)}", file=sys.stderr)
        return 2
    if not conflicts_path.exists():
        print(f"Conflict registry not found: {display_path(conflicts_path, ROOT)}", file=sys.stderr)
        return 2
    try:
        conflict_registry = json.loads(conflicts_path.read_text(encoding="utf-8"))
        validate_conflict_registry(conflict_registry)
    except (json.JSONDecodeError, OSError, UnicodeError, ValueError) as exc:
        print(f"Invalid conflict registry {display_path(conflicts_path, ROOT)}: {exc}", file=sys.stderr)
        return 1
    conflicts_by_match: dict[tuple[str, str], list[dict]] = {}
    for entry in conflict_registry:
        key = (entry["match"]["canonical_name"], entry["match"]["source_url"])
        conflicts_by_match.setdefault(key, []).append(entry["conflict"])
    try:
        with input_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                print(f"Normalization failed: CSV has no header: {display_path(input_path, ROOT)}", file=sys.stderr)
                return 1
            required_columns = {"name", "source_url", "retrieved_at"}
            missing_columns = sorted(required_columns - set(reader.fieldnames))
            if missing_columns:
                print(
                    f"Normalization failed: CSV missing columns: {', '.join(missing_columns)}",
                    file=sys.stderr,
                )
                return 1
            rows = list(enumerate(reader, start=2))
    except (csv.Error, OSError, UnicodeError) as exc:
        print(f"Normalization failed reading {display_path(input_path, ROOT)}: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print(f"Normalization failed: CSV contains no data rows: {display_path(input_path, ROOT)}", file=sys.stderr)
        return 1

    row_keys = Counter(
        ((row.get("name") or "").strip(), (row.get("source_url") or "").strip())
        for _, row in rows
    )
    registry_errors: list[str] = []
    for key, annotations in conflicts_by_match.items():
        if len(annotations) != 1:
            registry_errors.append(f"Conflict registry matches {key!r} more than once")
        if row_keys[key] == 0:
            registry_errors.append(f"Conflict registry orphan: no raw row matches {key!r}")
        elif row_keys[key] > 1:
            registry_errors.append(f"Conflict registry is ambiguous: {row_keys[key]} raw rows match {key!r}")
    if registry_errors:
        for error in registry_errors:
            print(error, file=sys.stderr)
        print("Normalization failed; output was not replaced", file=sys.stderr)
        return 1

    records = []
    errors = []
    for line_number, row in rows:
        key = ((row.get("name") or "").strip(), (row.get("source_url") or "").strip())
        record = normalize_manual_row(row, conflict_annotations=conflicts_by_match.get(key, []))
        try:
            validate_record(record)
        except ValueError as exc:
            if args.skip_invalid:
                print(f"Skipping {display_path(input_path, ROOT)}:{line_number}: {exc}", file=sys.stderr)
                continue
            errors.append(f"{input_path}:{line_number}: {exc}")
            continue
        records.append(record)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("Normalization failed; output was not replaced", file=sys.stderr)
        return 1
    if not records:
        print("Normalization failed: no valid records; output was not replaced", file=sys.stderr)
        return 1
    try:
        validate_unique_cafe_ids(records, "manual normalization")
    except ValueError as exc:
        print(f"Normalization failed: {exc}; output was not replaced", file=sys.stderr)
        return 1

    try:
        count = write_jsonl(output_path, records)
    except AtomicDurabilityError as exc:
        print(f"Manual output durability failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Manual output failed before replacement: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {count} normalized manual records to {display_path(output_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
