#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.schema import today_iso


ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.types",
        "places.googleMapsUri",
        "places.websiteUri",
        "places.regularOpeningHours",
        "places.priceLevel",
        "places.rating",
        "places.userRatingCount",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect cafes from Google Places Text Search when API access is available.")
    parser.add_argument("--query", default="不限時咖啡廳 台北")
    parser.add_argument("--output", default="data/raw/google_places_taipei_sample.json")
    parser.add_argument("--max-result-count", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def build_body(query: str, max_result_count: int) -> dict:
    return {
        "textQuery": query,
        "languageCode": "zh-TW",
        "regionCode": "TW",
        "includedType": "cafe",
        "maxResultCount": max_result_count,
        "locationRestriction": {
            "rectangle": {
                "low": {"latitude": 24.95, "longitude": 121.45},
                "high": {"latitude": 25.20, "longitude": 121.65},
            }
        },
    }


def fetch_places(api_key: str, body: dict) -> dict:
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    args = parse_args()
    body = build_body(args.query, args.max_result_count)
    if args.dry_run:
        print(json.dumps({"endpoint": ENDPOINT, "field_mask": FIELD_MASK, "body": body}, ensure_ascii=False, indent=2))
        return 0

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("GOOGLE_MAPS_API_KEY is not set; Google Places collection is optional and was skipped.", file=sys.stderr)
        return 2

    data = fetch_places(api_key, body)
    data["_collection"] = {
        "source": "google_places",
        "query": args.query,
        "retrieved_at": today_iso(),
        "field_mask": FIELD_MASK,
    }
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(data.get('places', []))} Google Places results to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

