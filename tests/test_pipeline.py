import unittest

from cafe_work_finder.dedupe import find_duplicate_candidates
from cafe_work_finder.normalize import normalize_manual_row, stable_cafe_id
from cafe_work_finder.schema import validate_record


class PipelineTests(unittest.TestCase):
    def test_manual_row_normalizes_into_canonical_record(self):
        row = {
            "name": "Sugar Man Cafe",
            "branch_name": "",
            "city": "Taipei",
            "district": "Da'an",
            "address": "",
            "lat": "",
            "lng": "",
            "unlimited_time": "yes",
            "outlets": "some",
            "wifi": "yes",
            "quietness": "quiet",
            "seat_comfort": "unknown",
            "meeting_suitability": "medium",
            "solo_work_suitability": "high",
            "study_suitability": "high",
            "online_meeting_suitability": "medium",
            "long_stay_suitability": "high",
            "opening_hours": "14:00-04:00",
            "minimum_order": "one drink",
            "price_level": "",
            "food_available": "yes",
            "reservation": "unknown",
            "source_url": "https://www.dcard.tw/f/food/p/241838488",
            "source_title": "台北讀書/辦公咖啡廳",
            "source_type": "forum",
            "published_at": "",
            "retrieved_at": "2026-06-01",
            "confidence": "medium",
            "confidence_notes": "Public Dcard post lists work-friendly details; branch/address still need verification.",
            "notes": "Deep-hours cafe mentioned as quiet in source.",
        }

        record = normalize_manual_row(row)

        self.assertEqual(record["canonical_name"], "Sugar Man Cafe")
        self.assertEqual(record["work_attributes"]["unlimited_time"], "yes")
        self.assertEqual(record["work_attributes"]["wifi"], "yes")
        self.assertEqual(record["source_links"][0]["url"], row["source_url"])
        self.assertEqual(record["overall_confidence"], "medium")
        validate_record(record)

    def test_stable_cafe_id_uses_name_city_district_and_address(self):
        first = stable_cafe_id("玖仰茶食文化", "Taipei", "Da'an", "台北市大安區永康街9-1號")
        second = stable_cafe_id(" 玖仰茶食文化 ", "Taipei", "Da'an", "台北市大安區永康街9-1號")

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("manual-"))

    def test_validate_record_rejects_missing_sources(self):
        record = normalize_manual_row(
            {
                "name": "No Source Cafe",
                "branch_name": "",
                "city": "Taipei",
                "district": "Zhongshan",
                "address": "",
                "lat": "",
                "lng": "",
                "unlimited_time": "unknown",
                "outlets": "unknown",
                "wifi": "unknown",
                "quietness": "unknown",
                "seat_comfort": "unknown",
                "meeting_suitability": "unknown",
                "solo_work_suitability": "unknown",
                "study_suitability": "unknown",
                "online_meeting_suitability": "unknown",
                "long_stay_suitability": "unknown",
                "opening_hours": "",
                "minimum_order": "",
                "price_level": "",
                "food_available": "unknown",
                "reservation": "unknown",
                "source_url": "",
                "source_title": "",
                "source_type": "",
                "published_at": "",
                "retrieved_at": "2026-06-01",
                "confidence": "low",
                "confidence_notes": "",
                "notes": "",
            }
        )

        with self.assertRaises(ValueError):
            validate_record(record)

    def test_duplicate_candidates_include_nearby_similar_names(self):
        first = normalize_manual_row(
            {
                "name": "Hoto Cafe",
                "branch_name": "",
                "city": "Taipei",
                "district": "Zhongshan",
                "address": "Taipei Zhongshan",
                "lat": "25.0521",
                "lng": "121.5211",
                "unlimited_time": "yes",
                "outlets": "some",
                "wifi": "yes",
                "quietness": "quiet",
                "seat_comfort": "unknown",
                "meeting_suitability": "medium",
                "solo_work_suitability": "high",
                "study_suitability": "high",
                "online_meeting_suitability": "medium",
                "long_stay_suitability": "high",
                "opening_hours": "",
                "minimum_order": "one drink",
                "price_level": "",
                "food_available": "unknown",
                "reservation": "unknown",
                "source_url": "https://www.dcard.tw/f/food/p/241838488",
                "source_title": "台北讀書/辦公咖啡廳",
                "source_type": "forum",
                "published_at": "",
                "retrieved_at": "2026-06-01",
                "confidence": "medium",
                "confidence_notes": "",
                "notes": "",
            }
        )
        second = dict(first)
        second["cafe_id"] = "osm-node-123"
        second["canonical_name"] = "HOTO CAFE"
        second["coordinates"] = {"lat": 25.0522, "lng": 121.5212}
        second["external_ids"] = {"osm": "node/123"}

        duplicates = find_duplicate_candidates([first, second])

        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["reason"], "similar_name_nearby")


if __name__ == "__main__":
    unittest.main()
