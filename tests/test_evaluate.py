import json
import tempfile
import unittest
from pathlib import Path

from eval.evaluate import (
    evaluate_results,
    extract_prediction_fields,
    normalize_category,
    normalize_department,
    normalize_urgency,
)


class TestEvaluate(unittest.TestCase):
    def test_normalize_department(self):
        # Case, whitespace, and separator variations
        self.assertEqual(normalize_department("Water Supply"), "water_supply")
        self.assertEqual(normalize_department("water_supply"), "water_supply")
        self.assertEqual(normalize_department("water-supply"), "water_supply")
        self.assertEqual(normalize_department("  Water   Supply  "), "water_supply")
        self.assertEqual(normalize_department("ROADS"), "roads")
        self.assertEqual(normalize_department("Electrical"), "electrical")
        self.assertEqual(normalize_department(None), "unknown")
        self.assertEqual(normalize_department(""), "unknown")
        self.assertEqual(normalize_department("   "), "unknown")

    def test_normalize_category(self):
        # Category normalization & synonyms consistent with backend.schema.ComplaintTriage
        self.assertEqual(normalize_category("roads"), "road_damage")
        self.assertEqual(normalize_category("road"), "road_damage")
        self.assertEqual(normalize_category("Road Damage"), "road_damage")
        self.assertEqual(normalize_category("road_damage"), "road_damage")
        self.assertEqual(normalize_category("water_supply"), "water_leak")
        self.assertEqual(normalize_category("water"), "water_leak")
        self.assertEqual(normalize_category("water-leak"), "water_leak")
        self.assertEqual(normalize_category("garbage"), "garbage")
        self.assertEqual(normalize_category("STREETLIGHT"), "streetlight")
        self.assertEqual(normalize_category(None), "unknown")
        self.assertEqual(normalize_category(""), "unknown")

    def test_normalize_urgency(self):
        # String urgency labels
        self.assertEqual(normalize_urgency("high")[0], "high")
        self.assertEqual(normalize_urgency(" MEDIUM ")[0], "medium")
        self.assertEqual(normalize_urgency("critical")[0], "critical")
        self.assertEqual(normalize_urgency("low")[0], "low")
        self.assertEqual(normalize_urgency(None)[0], "unknown")
        self.assertEqual(normalize_urgency("")[0], "unknown")

        # Documented numeric conversions (dashboard export format)
        self.assertEqual(normalize_urgency(5, allow_numeric_conversion=True)[0], "critical")
        self.assertEqual(normalize_urgency(4, allow_numeric_conversion=True)[0], "high")
        self.assertEqual(normalize_urgency(3, allow_numeric_conversion=True)[0], "medium")
        self.assertEqual(normalize_urgency(2, allow_numeric_conversion=True)[0], "low")
        self.assertEqual(normalize_urgency(1, allow_numeric_conversion=True)[0], "low")
        self.assertEqual(normalize_urgency("4", allow_numeric_conversion=True)[0], "high")

        # Strict mode (no numeric conversion)
        self.assertEqual(normalize_urgency(4, allow_numeric_conversion=False)[0], "unknown")
        self.assertEqual(normalize_urgency("4", allow_numeric_conversion=False)[0], "unknown")

    def test_extract_prediction_fields(self):
        # Root-level model output
        pred_root = {
            "department": "Water Supply",
            "category": "water_leak",
            "urgency": "high",
        }
        dept, cat, urg, is_num = extract_prediction_fields(pred_root)
        self.assertEqual(dept, "Water Supply")
        self.assertEqual(cat, "water_leak")
        self.assertEqual(urg, "high")
        self.assertFalse(is_num)

        # Nested prediction object
        pred_nested = {
            "prediction": {
                "department": "Roads",
                "category": "road_damage",
                "urgency": "critical",
            }
        }
        dept, cat, urg, is_num = extract_prediction_fields(pred_nested)
        self.assertEqual(dept, "Roads")
        self.assertEqual(cat, "road_damage")
        self.assertEqual(urg, "critical")
        self.assertFalse(is_num)

        # Dashboard export with numeric severity
        pred_dash = {
            "department": "sanitation",
            "category": "garbage",
            "severity": 4,
        }
        dept, cat, urg, is_num = extract_prediction_fields(pred_dash)
        self.assertEqual(dept, "sanitation")
        self.assertEqual(cat, "garbage")
        self.assertEqual(urg, "high")
        self.assertTrue(is_num)

        # Missing / None prediction
        dept, cat, urg, is_num = extract_prediction_fields(None)
        self.assertIsNone(dept)
        self.assertIsNone(cat)
        self.assertIsNone(urg)
        self.assertFalse(is_num)

    def test_evaluate_results_independent_metrics_and_missing(self):
        ground_truth = [
            {
                "id": "T-1",
                "language": "en",
                "text": "Water leaking",
                "expected": {"department": "Water Supply", "category": "water_leak", "severity": "high"},
            },
            {
                "id": "T-2",
                "language": "en",
                "text": "Pothole on street",
                "expected": {"department": "Roads", "category": "road_damage", "severity": "critical"},
            },
            {
                "id": "T-3",
                "language": "hi",
                "text": "Garbage not picked",
                "expected": {"department": "Sanitation", "category": "garbage", "severity": "medium"},
            },
            {
                "id": "T-4",
                "language": "mr",
                "text": "Missing prediction complaint",
                "expected": {"department": "Electrical", "category": "streetlight", "severity": "low"},
            },
        ]

        predictions = [
            # T-1: Everything matches (with whitespace/case differences in department)
            {
                "id": "T-1",
                "department": "water_supply",
                "category": "water_leak",
                "urgency": "high",
            },
            # T-2: Dept and category match, but urgency differs
            {
                "id": "T-2",
                "department": "roads",
                "category": "roads",  # synonym normalized to road_damage
                "urgency": "medium",  # expected critical -> urgency error
            },
            # T-3: Dept wrong, category match, urgency match
            {
                "id": "T-3",
                "department": "unknown",  # dept error
                "category": "garbage",
                "urgency": "medium",
            },
            # T-4 is missing from predictions
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.json"
            pred_file = Path(tmpdir) / "results.json"

            with open(data_file, "w") as f:
                json.dump(ground_truth, f)
            with open(pred_file, "w") as f:
                json.dump(predictions, f)

            metrics = evaluate_results(data_file=str(data_file), results_file=str(pred_file), verbose=False)

            # Total & Missing counts
            self.assertEqual(metrics["total"], 4)
            self.assertEqual(metrics["missing_count"], 1)

            # Department: T-1 and T-2 match (2/4 = 50%)
            self.assertEqual(metrics["dept_correct"], 2)
            self.assertAlmostEqual(metrics["dept_accuracy"], 0.5)
            self.assertEqual(len(metrics["dept_errors"]), 2)  # T-3 and T-4

            # Category: T-1, T-2, T-3 match (3/4 = 75%)
            self.assertEqual(metrics["cat_correct"], 3)
            self.assertAlmostEqual(metrics["cat_accuracy"], 0.75)
            self.assertEqual(len(metrics["cat_errors"]), 1)  # T-4 (missing)

            # Urgency: T-1 and T-3 match independently (2/4 = 50%)
            self.assertEqual(metrics["urgency_correct"], 2)
            self.assertAlmostEqual(metrics["urgency_accuracy"], 0.5)
            self.assertEqual(len(metrics["urgency_errors"]), 2)  # T-2 and T-4

            # Combined Routing: T-1 and T-2 have both dept and cat correct (2/4 = 50%)
            self.assertEqual(metrics["routed_correctly"], 2)
            self.assertAlmostEqual(metrics["routing_accuracy"], 0.5)


if __name__ == "__main__":
    unittest.main()
