"""
Improved model for the Student Early-Warning NLP Engine (Week 3-4).

Approach: pretrained sentence-transformer embeddings (all-MiniLM-L6-v2)
+ Logistic Regression head, trained separately for category and urgency.

Same classifier family as the Week 1-2 baseline (TF-IDF + Logistic Regression)
so the comparison isolates the effect of the representation (embeddings vs
TF-IDF) rather than the effect of switching classifiers.

Requires embeddings to already be generated (run embed.py first).

Usage:
    python embed.py
    python improved_model.py
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

EMBED_DIR = Path(__file__).resolve().parent / "embeddings"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
MODELS_DIR = Path(__file__).resolve().parent / "saved"
MODELS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


def load_split(split_name: str):
    X = np.load(EMBED_DIR / f"{split_name}_embeddings.npy")
    y_df = pd.read_csv(EMBED_DIR / f"{split_name}_labels.csv", keep_default_na=False)
    return X, y_df


def train_and_evaluate(target_col: str, label: str):
    X_train, train_df = load_split("train")
    X_val, val_df = load_split("val")
    X_test, test_df = load_split("test")

    y_train = train_df[target_col]
    y_val = val_df[target_col]
    y_test = test_df[target_col]

    clf = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )
    clf.fit(X_train, y_train)

    print(f"\n{'='*60}\nIMPROVED MODEL (embeddings) — {label} classification\n{'='*60}")

    for split_name, X, y in [("Validation", X_val, y_val), ("Test", X_test, y_test)]:
        preds = clf.predict(X)
        report = classification_report(y, preds, zero_division=0)
        print(f"\n--- {split_name} set ---")
        print(report)

        if split_name == "Test":
            report_dict = classification_report(y, preds, zero_division=0, output_dict=True)
            cm = confusion_matrix(y, preds, labels=sorted(y.unique()))
            cm_df = pd.DataFrame(cm, index=sorted(y.unique()), columns=sorted(y.unique()))

            pd.DataFrame(report_dict).transpose().to_csv(
                RESULTS_DIR / f"improved_{target_col}_test_report.csv"
            )
            cm_df.to_csv(RESULTS_DIR / f"improved_{target_col}_confusion_matrix.csv")

    joblib.dump(clf, MODELS_DIR / f"improved_{target_col}.joblib")
    print(f"Saved model -> {MODELS_DIR / f'improved_{target_col}.joblib'}")

    return clf


if __name__ == "__main__":
    train_and_evaluate("category", "Category")
    train_and_evaluate("urgency", "Urgency")