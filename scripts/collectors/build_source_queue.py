#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a manually reviewable source discovery queue from search seeds.")
    parser.add_argument("--input", default="data/raw/source_seed_queries.csv")
    parser.add_argument("--output", default="data/processed/source_review_queue.csv")
    return parser.parse_args()


def search_url(query: str) -> str:
    return "https://www.google.com/search?" + urllib.parse.urlencode({"q": query})


def main() -> int:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            query = row["query"].strip()
            rows.append(
                {
                    "query": query,
                    "source_category": row.get("source_category", "").strip(),
                    "city": row.get("city", "").strip(),
                    "status": row.get("status", "manual_review").strip(),
                    "search_url": search_url(query),
                    "notes": row.get("notes", "").strip(),
                }
            )

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["query", "source_category", "city", "status", "search_url", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} source review rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

