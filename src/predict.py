from pathlib import Path

import joblib

from src.preprocessing import clean_text
from src.risk_rules import detect_risk_indicators


# --------------------------------------------------
# 1. Model paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "models" / "fake_job_model.pkl"
VECTORIZER_PATH = PROJECT_ROOT / "models" / "tfidf_vectorizer.pkl"


# --------------------------------------------------
# 2. Load trained model and vectorizer
# --------------------------------------------------

model = joblib.load(MODEL_PATH)
tfidf = joblib.load(VECTORIZER_PATH)


# --------------------------------------------------
# 3. Predict a job advertisement
# --------------------------------------------------

def predict_job(text):
    """
    Predict whether a job advertisement is legitimate
    or potentially fraudulent.
    """

    # Clean the input text
    cleaned_text = clean_text(text)

    # Convert text into TF-IDF features
    text_tfidf = tfidf.transform([cleaned_text])

    # Make prediction
    prediction = model.predict(text_tfidf)[0]

    # Get probability for fraudulent class
    probability = model.predict_proba(text_tfidf)[0][1]

    if prediction == 1:
        label = "Potentially Fraudulent"
    else:
        label = "Likely Legitimate"

    risk_indicators = detect_risk_indicators(text)
    
    return {
        "label": label,
        "prediction": int(prediction),
        "fraud_probability": float(probability),
        "indicators": get_indicators(text),
        "risk_indicators": detect_risk_indicators(text)
    }

def get_indicators(text, top_n=5):
    """
    Identify words or phrases that contribute strongly
    toward the fraudulent class.
    """

    cleaned_text = clean_text(text)

    text_tfidf = tfidf.transform([cleaned_text])

    feature_names = tfidf.get_feature_names_out()
    coefficients = model.coef_[0]
    feature_values = text_tfidf.toarray()[0]

    contributions = feature_values * coefficients

    fraudulent_indices = [
        i for i, value in enumerate(contributions)
        if value > 0
    ]

    fraudulent_indices = sorted(
        fraudulent_indices,
        key=lambda i: contributions[i],
        reverse=True
    )

    indicators = [
        feature_names[i]
        for i in fraudulent_indices[:top_n]
    ]

    return indicators