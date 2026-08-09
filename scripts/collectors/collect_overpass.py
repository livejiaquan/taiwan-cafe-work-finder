#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.schema import today_iso


DEFAULT_BBOX = "24.95,121.45,25.20,121.65"
DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"


def build_query(bbox: str) -> str:
    south, west, north, east = [part.strip() for part in bbox.split(",")]
    return f"""[out:json][timeout:25];
(
  node["amenity"="cafe"]({south},{west},{north},{east});
  way["amenity"="cafe"]({south},{west},{north},{east});
  relation["amenity"="cafe"]({south},{west},{north},{east});
);
out center tags qt;
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public cafe POIs from Overpass.")
    parser.add_argument("--bbox", default=DEFAULT_BBOX, help="south,west,north,east. Default covers greater Taipei core.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--output", default="data/raw/overpass_taipei_sample.json")
    parser.add_argument("--query-output", default="data/raw/overpass_taipei_query.overpassql")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def fetch_overpass(endpoint: str, query: str) -> dict:
    payload = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "taiwan-cafe-work-finder/phase1 contact:local-research",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    args = parse_args()
    query = build_query(args.bbox)
    query_path = ROOT / args.query_output
    query_path.parent.mkdir(parents=True, exist_ok=True)
    query_path.write_text(query, encoding="utf-8")
    if args.dry_run:
        print(query)
        print(f"Wrote query to {args.query_output}")
        return 0

    data = fetch_overpass(args.endpoint, query)
    data["_collection"] = {
        "source": "overpass",
        "endpoint": args.endpoint,
        "bbox": args.bbox,
        "retrieved_at": today_iso(),
    }
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(data.get('elements', []))} Overpass elements to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

