import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def normalize_text(text):
    """
    Normalize job advertisement text before similarity comparison.
    """

    if not isinstance(text, str):
        return ""

    text = text.lower()

    # Remove email addresses
    text = re.sub(r"\S+@\S+", " ", text)

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", " ", text)

    # Remove punctuation
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_duplicate_index(job_texts):
    """
    Build a TF-IDF index from existing job advertisements.
    """

    normalized_jobs = [
        normalize_text(text)
        for text in job_texts
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_features=30000
    )

    job_matrix = vectorizer.fit_transform(normalized_jobs)

    return vectorizer, job_matrix


def find_most_similar_job(
    job_text,
    vectorizer,
    job_matrix,
    job_texts,
    threshold=0.85
):
    """
    Compare a new job advertisement against the existing
    job advertisement collection.
    """

    normalized_text = normalize_text(job_text)

    if not normalized_text:
        return {
            "is_duplicate": False,
            "similarity": 0.0,
            "matched_index": None,
            "matched_text": None
        }

    query_vector = vectorizer.transform(
        [normalized_text]
    )

    similarities = cosine_similarity(
        query_vector,
        job_matrix
    )[0]

    best_index = similarities.argmax()
    best_similarity = float(similarities[best_index])

    return {
        "is_duplicate": best_similarity >= threshold,
        "similarity": best_similarity,
        "matched_index": int(best_index),
        "matched_text": job_texts[best_index]
    }

def calculate_similarity(text1, text2):
    """
    Calculate cosine similarity between two job advertisements.
    Useful for comparing two specific advertisements directly.
    """

    normalized_text1 = normalize_text(text1)
    normalized_text2 = normalize_text(text2)

    if not normalized_text1 or not normalized_text2:
        return 0.0

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    vectors = vectorizer.fit_transform([
        normalized_text1,
        normalized_text2
    ])

    similarity = cosine_similarity(
        vectors[0:1],
        vectors[1:2]
    )[0][0]

    return float(similarity)