# Scamwatch-informed warning patterns for job advertisements.
#
# These rules are screening prompts, not proof of fraud. Scamwatch describes
# several warning signs as combinations of behaviours; "requires_any" keeps
# weaker phrases such as remote work or no experience from triggering alone.

RISK_PATTERNS = {
    "upfront_payment": {
        "weight": 40,
        "patterns": [
            "send money",
            "pay a fee",
            "registration fee",
            "recruitment fee",
            "upfront payment",
            "up-front payment",
            "payment before you start",
            "pay before starting",
            "pay for training materials",
            "training materials fee",
            "pay to unlock tasks",
            "top up your account",
            "top-up your account",
            "recharge your account",
            "top up your cryptocurrency account",
            "pay to withdraw",
            "pay to release your earnings",
        ],
    },

    "money_or_package_transfer": {
        "weight": 40,
        "patterns": [
            "receive money into your personal bank account",
            "use your personal bank account to receive money",
            "transfer money on behalf of",
            "transfer money to other accounts",
            "move money through your account",
            "receive packages on behalf of",
            "reship packages",
            "forward packages",
        ],
    },

    "high_income_low_effort": {
        "weight": 30,
        "patterns": [
            "high income",
            "high pay",
            "high salary",
            "guaranteed income",
            "guaranteed earnings",
            "easy money",
        ],
        "requires_any": [
            "little effort",
            "little work",
            "easy tasks",
            "simple tasks",
            "few hours a day",
            "few hours each day",
            "no experience",
            "no qualifications",
        ],
    },

    "no_experience_remote_work": {
        "weight": 15,
        "patterns": [
            "no experience required",
            "no experience necessary",
            "no previous experience",
            "don't need any previous experience",
            "do not need any previous experience",
            "without experience",
        ],
        "requires_any": [
            "work from home",
            "remote position",
            "fully remote",
            "high pay",
            "high salary",
            "high income",
            "little effort",
        ],
    },

    "urgent_recruitment": {
        "weight": 10,
        "patterns": [
            "limited positions",
            "only 20 positions",
            "only 25 positions",
            "act now",
            "apply immediately",
            "start immediately",
        ],
    },

    "quick_hiring_no_interview": {
        "weight": 25,
        "patterns": [
            "no interview required",
            "no interview needed",
            "without an interview",
            "hiring process is quick",
            "immediate hiring",
        ],
    },

    "minimal_application": {
        "weight": 15,
        "patterns": [
            "reply interested",
            "respond with interested",
            "respond with something like",
            "just reply interested",
        ],
    },

    "task_based_work": {
        "weight": 15,
        "patterns": [
            "rate products",
            "rating products",
            "optimise product listings",
            "optimize product listings",
            "complete tasks to earn commission",
        ],
    },
}


def detect_risk_indicators(text):
    """
    Detect Scamwatch-informed warning patterns in a job advertisement.

    Returns:
        A list of dictionaries containing:
        - category
        - phrase
        - weight

    A match is a prompt for further checking, not a determination that a job
    or employer is fraudulent.
    """

    text_lower = text.lower()
    matches = []

    for category, details in RISK_PATTERNS.items():
        required_context = details.get("requires_any", [])
        if required_context and not any(
            phrase in text_lower for phrase in required_context
        ):
            continue

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
    Calculate a heuristic rule-based score from 0 to 100.

    Each category is counted once. The weights are hand-set heuristics and
    have not been statistically calibrated against a labelled validation set.
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
