"""
Compares the Week 1-2 baseline (TF-IDF + LogReg) against the Week 3-4
improved model (sentence embeddings + LogReg) on test-set metrics.

Reads the *_test_report.csv files already saved by baseline.py and
improved_model.py, and produces one combined comparison table per task.

Usage:
    python compare_models.py
"""

import pandas as pd
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def compare(target_col: str, label: str):
    baseline = pd.read_csv(RESULTS_DIR / f"baseline_{target_col}_test_report.csv", index_col=0)
    improved = pd.read_csv(RESULTS_DIR / f"improved_{target_col}_test_report.csv", index_col=0)

    combined = pd.DataFrame({
        "baseline_f1": baseline["f1-score"],
        "improved_f1": improved["f1-score"],
    })
    combined["f1_change"] = combined["improved_f1"] - combined["baseline_f1"]

    print(f"\n{'='*70}\n{label} — Baseline (TF-IDF) vs Improved (Embeddings)\n{'='*70}")
    print(combined.round(3).to_string())

    combined.round(4).to_csv(RESULTS_DIR / f"comparison_{target_col}.csv")
    print(f"Saved -> {RESULTS_DIR / f'comparison_{target_col}.csv'}")

    macro_baseline = baseline.loc["macro avg", "f1-score"]
    macro_improved = improved.loc["macro avg", "f1-score"]
    acc_baseline = baseline.loc["accuracy", "f1-score"]
    acc_improved = improved.loc["accuracy", "f1-score"]

    print(f"\nAccuracy:  baseline={acc_baseline:.3f}  improved={acc_improved:.3f}")
    print(f"Macro F1:  baseline={macro_baseline:.3f}  improved={macro_improved:.3f}")


if __name__ == "__main__":
    compare("category", "Category")
    compare("urgency", "Urgency")