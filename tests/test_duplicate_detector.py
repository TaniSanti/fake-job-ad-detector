import unittest
from unittest.mock import patch

from src.duplicate_detector import calculate_similarity
from src.input_validation import InsufficientInformationError, is_sufficient_advertisement


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
    def test_similar_ads_reach_moderate_similarity_band(self):
        score = calculate_similarity(*SIMILAR_ADS)
        print(f"Near-duplicate pair similarity: {score:.4f}")
        self.assertGreaterEqual(score, 0.70)
        self.assertLess(score, 0.90)

    def test_unrelated_ads_stay_below_moderate_similarity_threshold(self):
        score = calculate_similarity(*UNRELATED_ADS)
        print(f"Unrelated pair similarity: {score:.4f}")
        self.assertLess(score, 0.70)

    def test_empty_ad_is_rejected_without_similarity_score(self):
        with self.assertRaises(InsufficientInformationError):
            calculate_similarity("", "A job advertisement with some content.")

    def test_meaningful_existing_pairs_pass_content_validation(self):
        for text in (*SIMILAR_ADS, *UNRELATED_ADS):
            with self.subTest(text=text[:40]):
                self.assertTrue(is_sufficient_advertisement(text))

    def test_both_empty_inputs_are_rejected_before_vectorization(self):
        with patch("src.duplicate_detector.TfidfVectorizer") as vectorizer:
            with self.assertRaises(InsufficientInformationError):
                calculate_similarity("", "")
        vectorizer.assert_not_called()

    def test_one_empty_input_is_rejected_before_vectorization(self):
        with patch("src.duplicate_detector.TfidfVectorizer") as vectorizer:
            with self.assertRaises(InsufficientInformationError):
                calculate_similarity("", SIMILAR_ADS[0])
        vectorizer.assert_not_called()

    def test_both_very_short_inputs_are_rejected_before_vectorization(self):
        with patch("src.duplicate_detector.TfidfVectorizer") as vectorizer:
            with self.assertRaises(InsufficientInformationError):
                calculate_similarity("asds", "asd")
        vectorizer.assert_not_called()

    def test_one_insufficient_ad_is_rejected_before_vectorization(self):
        with patch("src.duplicate_detector.TfidfVectorizer") as vectorizer:
            with self.assertRaises(InsufficientInformationError):
                calculate_similarity("sads", SIMILAR_ADS[0])
        vectorizer.assert_not_called()

    def test_meaningless_repeated_text_is_rejected_before_vectorization(self):
        repeated_text = "advertisement " * 40
        with patch("src.duplicate_detector.TfidfVectorizer") as vectorizer:
            with self.assertRaises(InsufficientInformationError):
                calculate_similarity(repeated_text, SIMILAR_ADS[0])
        vectorizer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
