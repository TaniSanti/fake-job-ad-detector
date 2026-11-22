import unittest
from unittest.mock import patch

from src.input_validation import (
    MINIMUM_AD_WORDS,
    InsufficientInformationError,
    is_sufficient_advertisement,
)
from src.predict import predict_job


SUFFICIENT_AD = (
    "Retail assistant needed to welcome customers, answer product questions, "
    "replenish shelves, process payments, and keep the store organised. "
    "Weekend shifts are available. Previous retail experience is helpful, "
    "but training is provided. Apply with a resume."
)


class TestAdvertisementInputValidation(unittest.TestCase):
    def test_empty_input_is_insufficient(self):
        self.assertFalse(is_sufficient_advertisement(""))

    def test_whitespace_only_input_is_insufficient(self):
        self.assertFalse(is_sufficient_advertisement(" \n\t  "))

    def test_very_short_input_is_insufficient(self):
        self.assertFalse(is_sufficient_advertisement("sads"))

    def test_repeated_meaningless_text_is_insufficient(self):
        repeated_text = "advertisement " * 40
        self.assertFalse(is_sufficient_advertisement(repeated_text))

    def test_ad_below_configured_word_threshold_is_insufficient(self):
        words = [
            "experienced", "kitchen", "assistant", "preparing", "fresh",
            "meals", "maintaining", "cleanliness", "organising", "stock",
            "supporting", "customers", "following", "safety", "procedures",
            "coordinating", "daily", "service", "communicating",
        ]
        below_threshold = " ".join(words)
        self.assertEqual(MINIMUM_AD_WORDS, 20)
        self.assertEqual(len(below_threshold.split()), MINIMUM_AD_WORDS - 1)
        self.assertFalse(is_sufficient_advertisement(below_threshold))

    def test_ad_below_character_threshold_is_insufficient(self):
        short_text = "oak elm ash fir log pine ant bee fox cat dog pig cow ram yak hen rat bat owl elk"
        self.assertEqual(len(short_text.split()), MINIMUM_AD_WORDS)
        self.assertFalse(is_sufficient_advertisement(short_text))

    def test_sufficient_meaningful_advertisement_passes(self):
        self.assertTrue(is_sufficient_advertisement(SUFFICIENT_AD))

    def test_prediction_rejects_short_text_before_model_or_vectorizer(self):
        with (
            patch("src.predict.model.predict") as model_predict,
            patch("src.predict.model.predict_proba") as model_predict_proba,
            patch("src.predict.tfidf.transform") as vectorizer_transform,
        ):
            with self.assertRaises(InsufficientInformationError):
                predict_job("sads")

        model_predict.assert_not_called()
        model_predict_proba.assert_not_called()
        vectorizer_transform.assert_not_called()

    def test_sufficient_ad_still_uses_existing_model(self):
        result = predict_job(SUFFICIENT_AD)
        self.assertIn(result["label"], {
            "Likely Legitimate",
            "Potentially Fraudulent",
        })
        self.assertIn(result["prediction"], {0, 1})
        self.assertGreaterEqual(result["fraud_probability"], 0.0)
        self.assertLessEqual(result["fraud_probability"], 1.0)


if __name__ == "__main__":
    unittest.main()
