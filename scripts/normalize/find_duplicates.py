#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.dedupe import find_duplicate_candidates
from cafe_work_finder.io import read_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find likely duplicate cafe records.")
    parser.add_argument("--input", default="data/curated/cafes.seed.jsonl")
    parser.add_argument("--output", default="data/processed/duplicate_candidates.json")
    parser.add_argument("--distance-m", type=float, default=150)
    parser.add_argument("--similarity", type=float, default=0.9)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = read_jsonl(ROOT / args.input)
    candidates = find_duplicate_candidates(
        records,
        distance_threshold_m=args.distance_m,
        similarity_threshold=args.similarity,
    )
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Found {len(candidates)} duplicate candidate(s); wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

