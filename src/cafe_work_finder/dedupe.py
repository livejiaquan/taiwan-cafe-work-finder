from __future__ import annotations

import math
import re
from difflib import SequenceMatcher
from typing import Any


def normalized_name(value: object) -> str:
    text = str(value or "").casefold()
    return re.sub(r"[\s\W_]+", "", text)


def similarity(first: str, second: str) -> float:
    left = normalized_name(first)
    right = normalized_name(second)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left, right).ratio()


def distance_meters(first: dict[str, float] | None, second: dict[str, float] | None) -> float | None:
    if not first or not second:
        return None
    lat1 = math.radians(float(first["lat"]))
    lon1 = math.radians(float(first["lng"]))
    lat2 = math.radians(float(second["lat"]))
    lon2 = math.radians(float(second["lng"]))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    haversine = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 6371000 * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))


def shared_external_id(first: dict[str, Any], second: dict[str, Any]) -> str | None:
    first_ids = first.get("external_ids") or {}
    second_ids = second.get("external_ids") or {}
    for key, value in first_ids.items():
        if value and second_ids.get(key) == value:
            return key
    return None


def find_duplicate_candidates(
    records: list[dict[str, Any]],
    distance_threshold_m: float = 150,
    similarity_threshold: float = 0.9,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for index, first in enumerate(records):
        for second in records[index + 1 :]:
            shared_id = shared_external_id(first, second)
            if shared_id:
                candidates.append(
                    {
                        "record_ids": [first["cafe_id"], second["cafe_id"]],
                        "names": [first["canonical_name"], second["canonical_name"]],
                        "reason": f"shared_external_id:{shared_id}",
                        "distance_m": None,
                        "similarity": 1.0,
                    }
                )
                continue

            name_similarity = similarity(first.get("canonical_name"), second.get("canonical_name"))
            distance = distance_meters(first.get("coordinates"), second.get("coordinates"))
            if (
                distance is not None
                and distance <= distance_threshold_m
                and name_similarity >= similarity_threshold
            ):
                candidates.append(
                    {
                        "record_ids": [first["cafe_id"], second["cafe_id"]],
                        "names": [first["canonical_name"], second["canonical_name"]],
                        "reason": "similar_name_nearby",
                        "distance_m": round(distance, 2),
                        "similarity": round(name_similarity, 3),
                    }
                )
                continue

            first_address = normalized_name(first.get("address"))
            second_address = normalized_name(second.get("address"))
            if (
                first_address
                and second_address
                and first_address == second_address
                and name_similarity >= similarity_threshold
            ):
                candidates.append(
                    {
                        "record_ids": [first["cafe_id"], second["cafe_id"]],
                        "names": [first["canonical_name"], second["canonical_name"]],
                        "reason": "similar_name_same_address",
                        "distance_m": distance,
                        "similarity": round(name_similarity, 3),
                    }
                )
    return candidates

