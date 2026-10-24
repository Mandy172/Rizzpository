import unittest
from backend.schema import ComplaintTriage, compute_operational_confidence


class TestSchemaConfidence(unittest.TestCase):
    def test_high_confidence_clear_complaint(self):
        conf, needs_review = compute_operational_confidence(
            category="water_leak",
            department="Water Supply",
            urgency="high",
            text="Water is leaking continuously near the school gate on Tilak Road",
            location="Tilak Road school gate",
        )
        self.assertGreaterEqual(conf, 0.85)
        self.assertFalse(needs_review)

    def test_low_confidence_vague_input(self):
        conf, needs_review = compute_operational_confidence(
            category="other",
            department="unknown",
            urgency="medium",
            text="road bad",
            location="unknown",
        )
        self.assertLess(conf, 0.75)
        self.assertTrue(needs_review)

    def test_edge_case_ambiguous_category(self):
        # Open manhole categorized as 'other' routed to Drainage
        conf, needs_review = compute_operational_confidence(
            category="other",
            department="Drainage",
            urgency="critical",
            text="Footpath pe open manhole cover nahi hai",
            location="unknown",
        )
        self.assertLess(conf, 0.75)
        self.assertTrue(needs_review)

    def test_triage_model_populates_confidence(self):
        t = ComplaintTriage(
            category="road_damage",
            department="Roads",
            urgency="high",
            location="Shivaji Chowk",
            summary="Large pothole on main road",
        )
        t.populate_confidence(text="Pothole causing vehicles to swerve near Shivaji Chowk")
        self.assertIsNotNone(t.confidence)
        self.assertIsNotNone(t.needs_human_review)
        self.assertGreaterEqual(t.confidence, 0.85)
        self.assertFalse(t.needs_human_review)


if __name__ == "__main__":
    unittest.main()
