#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import AtomicDurabilityError, display_path, read_jsonl, write_text_atomic
from cafe_work_finder.publication import audit_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministically audit whether canonical cafe records meet the publication contract."
    )
    parser.add_argument("--input", default="data/curated/cafes.seed.jsonl")
    parser.add_argument(
        "--as-of",
        required=True,
        help="Required ISO audit date for reproducible results.",
    )
    parser.add_argument("--output", help="Write the JSON report to this path instead of stdout.")
    parser.add_argument(
        "--require-publishable",
        action="store_true",
        help="Exit 3 when the audit contains zero publishable records.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = ROOT / args.input
    if not input_path.exists():
        print(f"Input not found: {display_path(input_path, ROOT)}", file=sys.stderr)
        return 2

    try:
        records = read_jsonl(input_path)
        if not records:
            print(f"Publication audit failed: input is empty: {display_path(input_path, ROOT)}", file=sys.stderr)
            return 2
        report = audit_records(records, args.as_of, environment="production")
    except (OSError, ValueError, TypeError) as exc:
        print(f"Publication audit failed: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = ROOT / args.output
        try:
            write_text_atomic(output_path, rendered)
        except AtomicDurabilityError as exc:
            print(f"Publication audit output durability failed: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"Publication audit output failed: {exc}", file=sys.stderr)
            return 1
        summary = report["summary"]
        print(
            f"Audited {summary['total']} records: {summary['publishable']} publishable, "
            f"{summary['blocked']} blocked; wrote {display_path(output_path, ROOT)}"
        )
    else:
        print(rendered, end="")

    if args.require_publishable and report["summary"]["publishable"] == 0:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
