"""Lightweight content checks used before job-ad analysis."""
import re


# These module-level settings are intentionally easy to tune. A 30-word
# cutoff would reject the project's existing meaningful similarity examples
# (21–28 words), so the starting threshold is 20 words plus character and
# information-density checks.
MINIMUM_AD_WORDS = 20
MINIMUM_AD_CHARACTERS = 100
MINIMUM_MEANINGFUL_WORDS = 8
MINIMUM_UNIQUE_MEANINGFUL_WORDS = 8
MINIMUM_UNIQUE_WORD_RATIO = 0.4

MAIN_INSUFFICIENT_MESSAGE = (
    "Please enter a more complete job advertisement, including details such "
    "as job responsibilities, requirements or employment information, so "
    "the application can perform a meaningful assessment."
)
SIMILARITY_INSUFFICIENT_MESSAGE = (
    "Both advertisements must contain sufficient job-related content before "
    "their similarity can be assessed. Please provide more complete "
    "advertisement descriptions."
)

_WORD_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)
_COMMON_WORDS = frozenset(
    "a an and are as at be been by for from had has have in is it its of on "
    "or that the their they this to was were will with you your we our".split()
)


class InsufficientInformationError(ValueError):
    """Raised when text is too sparse for prediction or similarity analysis."""


def is_sufficient_advertisement(text):
    """Return whether text has enough length and lexical variety for analysis.

    This heuristic does not determine whether an advertisement is genuine or
    fraudulent. It only rejects empty, very short, or highly repetitive text.
    """
    if not isinstance(text, str):
        return False

    normalized = text.strip()
    if len(normalized) < MINIMUM_AD_CHARACTERS:
        return False

    words = [word.casefold() for word in _WORD_PATTERN.findall(normalized)]
    if len(words) < MINIMUM_AD_WORDS:
        return False

    meaningful_words = [
        word for word in words
        if len(word) >= 3 and word not in _COMMON_WORDS
    ]
    unique_meaningful_words = set(meaningful_words)
    if len(meaningful_words) < MINIMUM_MEANINGFUL_WORDS:
        return False
    if len(unique_meaningful_words) < MINIMUM_UNIQUE_MEANINGFUL_WORDS:
        return False
    if len(unique_meaningful_words) / len(meaningful_words) < MINIMUM_UNIQUE_WORD_RATIO:
        return False

    return True


def require_sufficient_advertisement(text):
    """Raise a friendly validation error unless the ad passes the heuristic."""
    if not is_sufficient_advertisement(text):
        raise InsufficientInformationError(MAIN_INSUFFICIENT_MESSAGE)
