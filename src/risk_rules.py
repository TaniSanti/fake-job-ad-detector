# Fraud-risk indicators for job advertisements

RISK_PATTERNS = {
    "bank_account": {
        "weight": 30,
        "patterns": [
            "bank account",
            "personal bank account",
            "account for receiving payments",
        ],
    },

    "payment_request": {
        "weight": 40,
        "patterns": [
            "send money",
            "pay a fee",
            "registration fee",
            "upfront payment",
            "payment required",
        ],
    },

    "no_experience": {
        "weight": 15,
        "patterns": [
            "no experience required",
            "no previous experience",
            "don't need any previous experience",
            "do not need any previous experience",
            "without experience",
        ],
    },

    "vague_remote_work": {
        "weight": 5,
        "patterns": [
            "work from home",
            "fully remote",
            "remote position",
        ],
    },

    "guaranteed_income": {
        "weight": 30,
        "patterns": [
            "guaranteed income",
            "guaranteed earnings",
            "easy money",
        ],
    },

    "urgent_recruitment": {
        "weight": 15,
        "patterns": [
            "limited positions",
            "act now",
            "apply immediately",
            "start immediately",
        ],
    },

    "minimal_application": {
        "weight": 20,
        "patterns": [
            "reply interested",
            "respond with interested",
            "respond with something like",
            "just reply",
        ],
    },
    "unpaid_internship": {
        "weight": 20,
        "patterns": [
            "unpaid internship",
            "unpaid position",
            "unpaid role",
            "this is an unpaid internship",
        ],
    },
    "certification_promise": {
        "weight": 10,
        "patterns": [
            "gain certifications",
            "gain certification",
            "along with certifications",
            "receive a certificate",
            "receive certification",
        ],
    },
    "vague_opportunity": {
        "weight": 10,
        "patterns": [
            "real-world experience",
            "real world experience",
            "skill development",
            "portfolio-building opportunities",
            "portfolio building opportunities",
        ],
    },
}


def detect_risk_indicators(text):
    """
    Detect potentially suspicious patterns in a job advertisement.

    Returns:
        A list of dictionaries containing:
        - category
        - phrase
        - weight
    """

    text_lower = text.lower()
    matches = []

    for category, details in RISK_PATTERNS.items():
        for pattern in details["patterns"]:
            if pattern in text_lower:
                matches.append({
                    "category": category,
                    "phrase": pattern,
                    "weight": details["weight"],
                })

    return matches

def calculate_risk_score(text):
    """
    Calculate a rule-based risk score from 0 to 100.

    Each risk category is counted only once to avoid
    double-counting multiple phrases from the same category.
    """

    matches = detect_risk_indicators(text)

    # Keep the highest weight for each category
    category_scores = {}

    for item in matches:
        category = item["category"]
        weight = item["weight"]

        if category not in category_scores:
            category_scores[category] = weight
        else:
            category_scores[category] = max(
                category_scores[category],
                weight
            )

    total_score = sum(category_scores.values())

    # Limit score to 100
    return min(total_score, 100)