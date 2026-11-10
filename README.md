# 🔍 Fake Job Advertisement Detector

A machine learning-based application for screening job advertisements and identifying potentially fraudulent or suspicious job postings.

The system combines **machine learning classification**, **rule-based risk detection**, and **duplicate/similarity detection** to provide a more comprehensive assessment of job advertisements.

> ⚠️ This tool is designed as a screening aid and does not provide definitive proof that a job advertisement is fraudulent.

---

## 📌 Overview

Fake and misleading job advertisements can make it difficult for job seekers to distinguish legitimate employment opportunities from potentially fraudulent postings.

This project was developed to explore how machine learning and text-based analysis can be used to assist with the initial screening of job advertisements.

Users can paste a complete job advertisement into the application and receive:

- An overall prediction
- Estimated fraud probability
- Rule-based risk indicators
- Duplicate/similarity analysis where applicable

---

## ✨ Features

### 🤖 Machine Learning Classification

The application uses a text classification model trained on job advertisement data to estimate whether a posting belongs to the legitimate or fraudulent class.

The model produces:

- **Likely Legitimate**
- **Potentially Fraudulent**
- Estimated fraud probability

### ⚠️ Rule-Based Risk Detection

The application also checks for specific patterns that may require additional attention.

Examples include:

- Requests for bank account information
- Payment-related language
- No-experience requirements
- Vague remote-work descriptions
- Minimal application instructions

These indicators are presented as potential risk signals rather than definitive evidence of fraud.

### 🔎 Duplicate and Similarity Detection

The system can compare job advertisements based on their textual similarity.

This can help identify cases where:

- The same advertisement appears under different company names
- Different job titles contain nearly identical descriptions
- A posting appears to have been reused or copied

### 🌐 Streamlit Web Application

The project includes a simple web interface that allows users to paste a job advertisement and analyse it without interacting directly with the machine learning code.

---

## 📊 Model Comparison

Both models were evaluated on the same stratified 80/20 train/test split of the dataset, using `random_state=42). TF-IDF was fitted on the training data only, with 20,000 maximum features and unigram/bigram features.

| Fraud-class metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Accuracy | **98.24%** | 98.15% |
| Precision | 76.70% | **96.52%** |
| Recall | **91.33%** | 64.16% |
| F1-score | **83.38%** | 77.08% |

The held-out test set contained **3,576 advertisements**: 3,403 legitimate and 173 fraudulent.

### Confusion matrices

Rows are actual classes and columns are predicted classes, ordered as `[Legitimate, Fraudulent]`.

**Logistic Regression**

```text
[[3355   48]
 [  15  158]]
```

**Random Forest**

```text
[[3399    4]
 [  62  111]]
```

Logistic Regression detected 158 of the 173 fraudulent advertisements and missed 15. Random Forest detected 111 and missed 62. Random Forest produced fewer false positives (4 versus 48), while Logistic Regression had higher fraud recall and F1-score. Logistic Regression remains the deployed model because this screening application should avoid missing potentially fraudulent ads. The benchmark does not establish that either model will perform the same way on future job advertisements; the test set contains only 173 fraudulent examples, and results are from one split.
