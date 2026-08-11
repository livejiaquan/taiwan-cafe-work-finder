#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from cafe_work_finder.io import AtomicDurabilityError, display_path, write_text_atomic
from cafe_work_finder.schema import is_iso_date_or_datetime, today_iso


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
out meta center qt;
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


def is_coordinate(value: object, lower: float, upper: float) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and lower <= float(value) <= upper
    )


def is_complete_cafe_element(element: object) -> bool:
    if not isinstance(element, dict):
        return False
    element_type = element.get("type")
    if element_type not in {"node", "way", "relation"}:
        return False
    element_id = element.get("id")
    if not isinstance(element_id, int) or isinstance(element_id, bool):
        return False
    if (
        not isinstance(element.get("timestamp"), str)
        or not element["timestamp"].strip()
        or not is_iso_date_or_datetime(element["timestamp"])
    ):
        return False
    tags = element.get("tags")
    if (
        not isinstance(tags, dict)
        or not all(isinstance(key, str) and isinstance(value, str) for key, value in tags.items())
        or tags.get("amenity") != "cafe"
    ):
        return False
    coordinates = element if element_type == "node" else element.get("center")
    if not isinstance(coordinates, dict):
        return False
    return is_coordinate(coordinates.get("lat"), -90, 90) and is_coordinate(
        coordinates.get("lon"), -180, 180
    )


def main() -> int:
    args = parse_args()
    query = build_query(args.bbox)
    query_path = ROOT / args.query_output
    query_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        write_text_atomic(query_path, query)
    except AtomicDurabilityError as exc:
        print(f"Overpass query output durability failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Overpass query output failed before replacement: {exc}", file=sys.stderr)
        return 1
    if args.dry_run:
        print(query)
        print(f"Wrote query to {args.query_output}")
        return 0

    try:
        data = fetch_overpass(args.endpoint, query)
    except Exception as exc:
        print(f"Overpass collection failed: {exc}; raw output was not replaced", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("Overpass collection failed: response root is not an object; raw output was not replaced", file=sys.stderr)
        return 1
    if any(data.get(field) for field in ("remark", "error", "errors")):
        print("Overpass collection failed: response contains an error/partial-result marker; raw output was not replaced", file=sys.stderr)
        return 1
    elements = data.get("elements")
    if not isinstance(elements, list) or not elements:
        print("Overpass collection failed: response has zero/invalid elements; raw output was not replaced", file=sys.stderr)
        return 1
    if not all(is_complete_cafe_element(element) for element in elements):
        print("Overpass collection failed: response contains incomplete/non-cafe elements; raw output was not replaced", file=sys.stderr)
        return 1
    element_keys = [(element["type"], element["id"]) for element in elements]
    if len(element_keys) != len(set(element_keys)):
        print("Overpass collection failed: response contains duplicate (type, id) elements; raw output was not replaced", file=sys.stderr)
        return 1
    data["_collection"] = {
        "source": "overpass",
        "endpoint": args.endpoint,
        "bbox": args.bbox,
        "retrieved_at": today_iso(),
    }
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        write_text_atomic(
            output_path,
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    except AtomicDurabilityError as exc:
        print(f"Overpass output durability failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Overpass output failed: {exc}; raw output was not replaced", file=sys.stderr)
        return 1
    print(f"Wrote {len(elements)} Overpass elements to {display_path(output_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
