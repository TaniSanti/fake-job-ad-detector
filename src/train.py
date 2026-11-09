from pathlib import Path

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from src.preprocessing import TEXT_COLUMNS, clean_text


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "fake_job_postings.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "fake_job_model.pkl"
VECTORIZER_PATH = PROJECT_ROOT / "models" / "tfidf_vectorizer.pkl"


# --------------------------------------------------
# 2. Load dataset
# --------------------------------------------------

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset loaded: {len(df)} job advertisements")


# --------------------------------------------------
# 3. Prepare text data
# --------------------------------------------------

print("Preparing text data...")

# Replace missing values
df[TEXT_COLUMNS] = df[TEXT_COLUMNS].fillna("")

# Combine the selected text fields
df["combined_text"] = (
    df["title"] + " " +
    df["company_profile"] + " " +
    df["description"] + " " +
    df["requirements"] + " " +
    df["benefits"]
)

# Clean the combined text
df["clean_text"] = df["combined_text"].apply(clean_text)


# --------------------------------------------------
# 4. Define features and target
# --------------------------------------------------

X = df["clean_text"]
y = df["fraudulent"]


# --------------------------------------------------
# 5. Split training and testing data
# --------------------------------------------------

print("Splitting dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Training records: {len(X_train)}")
print(f"Testing records: {len(X_test)}")


# --------------------------------------------------
# 6. TF-IDF feature extraction
# --------------------------------------------------

print("Creating TF-IDF features...")

tfidf = TfidfVectorizer(
    max_features=20000,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True
)

X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

print(f"TF-IDF training shape: {X_train_tfidf.shape}")
print(f"TF-IDF testing shape: {X_test_tfidf.shape}")


# --------------------------------------------------
# 7. Train and evaluate comparison models
# --------------------------------------------------

models = {
    "Logistic Regression": LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    ),
}

evaluation_results = {}

for model_name, candidate_model in models.items():
    print(f"\nTraining {model_name} model...")
    candidate_model.fit(X_train_tfidf, y_train)

    y_pred = candidate_model.predict(X_test_tfidf)

    evaluation_results[model_name] = {
        "model": candidate_model,
        "predictions": y_pred,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
    }

    print(f"{model_name} training completed.")


# --------------------------------------------------
# 8. Print comparison results
# --------------------------------------------------

for model_name, result in evaluation_results.items():
    print(f"\n===== {model_name} EVALUATION =====")
    print(f"Accuracy : {result['accuracy']:.4f}")
    print(f"Precision: {result['precision']:.4f}")
    print(f"Recall   : {result['recall']:.4f}")
    print(f"F1-score : {result['f1']:.4f}")

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        result["predictions"],
        labels=[0, 1],
        target_names=["Legitimate", "Fraudulent"],
        zero_division=0
    ))

    print("Confusion Matrix (rows=actual, columns=predicted; labels=[0, 1]):")
    print(confusion_matrix(
        y_test,
        result["predictions"],
        labels=[0, 1]
    ))


# --------------------------------------------------
# 9. Save the current deployed Logistic Regression model
# --------------------------------------------------

print("\nSaving Logistic Regression model and TF-IDF vectorizer...")

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

deployed_model = evaluation_results["Logistic Regression"]["model"]
joblib.dump(deployed_model, MODEL_PATH)
joblib.dump(tfidf, VECTORIZER_PATH)

print(f"Logistic Regression model saved to: {MODEL_PATH}")
print(f"Vectorizer saved to: {VECTORIZER_PATH}")

print("\nTraining and comparison pipeline completed successfully!")
