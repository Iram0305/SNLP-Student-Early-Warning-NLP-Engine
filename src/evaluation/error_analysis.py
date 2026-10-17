import numpy as np
import pandas as pd
import joblib
from pathlib import Path

EMBED_DIR = Path(__file__).resolve().parents[1] / "models" / "embeddings_v2"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models" / "saved"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_test_split():
    X = np.load(EMBED_DIR / "test_embeddings.npy")
    y_df = pd.read_csv(EMBED_DIR / "test_labels.csv", keep_default_na=False)
    return X, y_df


def analyze(target_col, label):
    X_test, test_df = load_test_split()
    clf = joblib.load(MODELS_DIR / f"week4_{target_col}.joblib")

    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)
    confidences = probs.max(axis=1)

    results = test_df.copy()
    results["predicted"] = preds
    results["confidence"] = confidences.round(3)
    results["correct"] = results[target_col] == results["predicted"]

    errors = results[~results["correct"]].sort_values("confidence", ascending=False)

    print(f"\n{'='*70}\nERROR ANALYSIS — {label}\n{'='*70}")
    print(f"Test set size: {len(results)}")
    print(f"Errors: {len(errors)}  ({len(errors) / len(results) * 100:.1f}%)")
    print(f"\nTop misclassifications (highest confidence wrong answers first):\n")

    for _, row in errors.head(10).iterrows():
        print(f"- text: {row['text'][:80]}")
        print(f"  true: {row[target_col]}  |  predicted: {row['predicted']}  |  confidence: {row['confidence']}")
        print()

    errors.to_csv(RESULTS_DIR / f"week5_{target_col}_errors.csv", index=False)
    results.to_csv(RESULTS_DIR / f"week5_{target_col}_all_predictions.csv", index=False)
    print(f"Saved -> results/week5_{target_col}_errors.csv")
    print(f"Saved -> results/week5_{target_col}_all_predictions.csv")

    low_conf = results[results["confidence"] < 0.5]
    print(f"\nLow-confidence predictions (<0.5): {len(low_conf)} ({len(low_conf) / len(results) * 100:.1f}%)")

    return errors


def robustness_check(target_col, label):
    X_test, test_df = load_test_split()
    clf = joblib.load(MODELS_DIR / f"week4_{target_col}.joblib")

    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)
    confidences = probs.max(axis=1)

    print(f"\n--- Robustness summary: {label} ---")
    print(f"Mean confidence (correct predictions): {confidences[preds == test_df[target_col]].mean():.3f}")
    wrong_mask = preds != test_df[target_col]
    if wrong_mask.sum() > 0:
        print(f"Mean confidence (wrong predictions): {confidences[wrong_mask].mean():.3f}")
    else:
        print("No wrong predictions on this split.")


if __name__ == "__main__":
    analyze("category", "Category")
    robustness_check("category", "Category")

    analyze("urgency", "Urgency")
    robustness_check("urgency", "Urgency")