import unittest

from src.duplicate_detector import calculate_similarity


SIMILAR_ADS = (
    "Customer service representative to answer customer questions by phone "
    "and email, resolve complaints, and record each interaction. Requires "
    "clear communication skills and two years of customer service experience.",
    "Customer service representative to answer customer questions by phone "
    "and email, resolve complaints, and record each interaction. Requires "
    "strong communication skills and three years of customer service experience.",
)

UNRELATED_ADS = (
    "Senior accountant needed to manage financial reporting, prepare monthly "
    "budgets, reconcile accounts, and support annual audits. Applicants need "
    "a bachelor's degree in accounting and experience with Xero.",
    "Seasonal orchard worker needed to harvest apples, prune trees, operate "
    "tractors, and pack fresh produce. Applicants need stamina and agricultural "
    "experience.",
)


class TestDuplicateDetector(unittest.TestCase):
    def test_near_duplicate_ads_reach_high_similarity_threshold(self):
        score = calculate_similarity(*SIMILAR_ADS)
        print(f"Near-duplicate pair similarity: {score:.4f}")
        self.assertGreaterEqual(score, 0.90)

    def test_unrelated_ads_stay_below_moderate_similarity_threshold(self):
        score = calculate_similarity(*UNRELATED_ADS)
        print(f"Unrelated pair similarity: {score:.4f}")
        self.assertLess(score, 0.70)

    def test_empty_ad_returns_zero_similarity(self):
        self.assertEqual(
            calculate_similarity("", "A job advertisement with some content."),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
