import unittest

from src.risk_rules import calculate_risk_score, detect_risk_indicators


class TestRiskRules(unittest.TestCase):
    def categories(self, text):
        return {
            item["category"]
            for item in detect_risk_indicators(text)
        }

    def test_upfront_recruitment_fee(self):
        self.assertIn(
            "upfront_payment",
            self.categories(
                "Applicants must pay an upfront recruitment fee before starting."
            ),
        )

    def test_cryptocurrency_account_top_up(self):
        self.assertIn(
            "upfront_payment",
            self.categories(
                "Top up your cryptocurrency account to unlock tasks."
            ),
        )

    def test_platform_account_top_up_using_cryptocurrency(self):
        self.assertIn(
            "upfront_payment",
            self.categories(
                "To unlock higher-value tasks and earn commission, "
                "top up your platform account using cryptocurrency."
            ),
        )

    def test_crypto_mention_without_top_up_is_not_flagged_as_payment(self):
        self.assertNotIn(
            "upfront_payment",
            self.categories(
                "The company accepts cryptocurrency payments from customers."
            ),
        )

    def test_high_income_with_little_effort(self):
        self.assertIn(
            "high_income_low_effort",
            self.categories("High income for little effort."),
        )

    def test_no_experience_with_remote_work(self):
        self.assertIn(
            "no_experience_remote_work",
            self.categories(
                "No experience required. This is a fully remote role."
            ),
        )

    def test_no_experience_alone_is_not_flagged(self):
        self.assertNotIn(
            "no_experience_remote_work",
            self.categories("No experience required."),
        )

    def test_work_from_home_alone_is_not_flagged(self):
        self.assertEqual(
            self.categories("Work from home in this experienced nursing role."),
            set(),
        )

    def test_quick_hiring_without_interview(self):
        self.assertIn(
            "quick_hiring_no_interview",
            self.categories(
                "The hiring process is quick and no interview is required."
            ),
        )

    def test_money_transfer_task(self):
        self.assertIn(
            "money_or_package_transfer",
            self.categories(
                "Receive money into your personal bank account, "
                "then transfer money to other accounts."
            ),
        )

    def test_suspicious_bsb_and_account_number_request(self):
        self.assertIn(
            "personal_bank_details_request",
            self.categories(
                "Provide your BSB and account number to proceed with recruitment."
            ),
        )

    def test_personal_banking_information_before_employment(self):
        self.assertIn(
            "personal_bank_details_request",
            self.categories(
                "Provide your banking information before employment."
            ),
        )

    def test_payroll_onboarding_request_is_not_flagged(self):
        self.assertNotIn(
            "personal_bank_details_request",
            self.categories(
                "During onboarding, provide your BSB and account number "
                "so payroll can deposit your wages."
            ),
        )

    def test_package_forwarding_task(self):
        self.assertIn(
            "money_or_package_transfer",
            self.categories(
                "Receive packages on behalf of the company and forward packages."
            ),
        )

    def test_product_rating_task(self):
        self.assertIn(
            "task_based_work",
            self.categories(
                "Earn commission by rating products and optimising product listings."
            ),
        )

    def test_product_rating_hyphenated_task(self):
        self.assertIn(
            "task_based_work",
            self.categories(
                "Complete product-rating tasks through our online platform."
            ),
        )

    def test_urgent_limited_positions(self):
        self.assertIn(
            "urgent_recruitment",
            self.categories(
                "Only 20 positions are available. Apply immediately."
            ),
        )

    def test_unpaid_internship_phrase_alone_is_not_flagged(self):
        self.assertEqual(
            self.categories("This is an unpaid internship."),
            set(),
        )

    def test_score_counts_each_category_once(self):
        self.assertEqual(
            calculate_risk_score("High income and high pay for little effort."),
            30,
        )


if __name__ == "__main__":
    unittest.main()
