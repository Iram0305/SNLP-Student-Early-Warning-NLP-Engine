"""
Baseline model for the Student Early-Warning NLP Engine.

Approach: TF-IDF features + Logistic Regression, trained SEPARATELY for:
  - category classification (5 concern categories + No_Concern)
  - urgency classification (Low / Medium / High / No_Concern)

This is the Week 1-2 baseline (per project handout Section 6: "Baseline +
Improved Approach"). A transformer/sentence-embedding approach will be
implemented as the improved model in Week 3-4.

Usage:
    python baseline.py
"""

import pandas as pd
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
MODELS_DIR = Path(__file__).resolve().parent / "saved"
MODELS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
            stop_words="english",
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",  # dataset is imbalanced across categories
            random_state=42,
        )),
    ])


def train_and_evaluate(target_col: str, label: str):
    train_df = pd.read_csv(DATA_DIR / "train.csv", keep_default_na=False)
    val_df = pd.read_csv(DATA_DIR / "val.csv", keep_default_na=False)
    test_df = pd.read_csv(DATA_DIR / "test.csv", keep_default_na=False)

    X_train, y_train = train_df["text"], train_df[target_col]
    X_val, y_val = val_df["text"], val_df[target_col]
    X_test, y_test = test_df["text"], test_df[target_col]

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    print(f"\n{'='*60}\nBASELINE — {label} classification\n{'='*60}")

    for split_name, X, y in [("Validation", X_val, y_val), ("Test", X_test, y_test)]:
        preds = pipeline.predict(X)
        report = classification_report(y, preds, zero_division=0)
        print(f"\n--- {split_name} set ---")
        print(report)

        if split_name == "Test":
            report_dict = classification_report(y, preds, zero_division=0, output_dict=True)
            cm = confusion_matrix(y, preds, labels=sorted(y.unique()))
            cm_df = pd.DataFrame(cm, index=sorted(y.unique()), columns=sorted(y.unique()))

            # save results
            pd.DataFrame(report_dict).transpose().to_csv(
                RESULTS_DIR / f"baseline_{target_col}_test_report.csv"
            )
            cm_df.to_csv(RESULTS_DIR / f"baseline_{target_col}_confusion_matrix.csv")

    joblib.dump(pipeline, MODELS_DIR / f"baseline_{target_col}.joblib")
    print(f"Saved model -> {MODELS_DIR / f'baseline_{target_col}.joblib'}")

    return pipeline


if __name__ == "__main__":
    train_and_evaluate("category", "Category")
    train_and_evaluate("urgency", "Urgency")
