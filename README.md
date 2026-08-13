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

## 📊 Model Performance

The final model was evaluated on a held-out test dataset.

| Metric | Score |
|---|---:|
| Accuracy | **98.24%** |
| Precision | **76.70%** |
| Recall | **91.33%** |
| F1-score | **83.38%** |

### Classification Report

| Class | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Legitimate | 0.99 | 0.99 | 0.99 |
| Fraudulent | 0.77 | 0.91 | 0.83 |

The test set contained **3,576 advertisements**, including 3,403 legitimate and 173 fraudulent advertisements.

### Confusion Matrix

```text
                 Predicted
              Legitimate  Fraudulent

Actual
Legitimate       3355        48
Fraudulent         15       158