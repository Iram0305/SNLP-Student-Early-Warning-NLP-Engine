import pandas as pd
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def compare(target_col, label):
    baseline = pd.read_csv(RESULTS_DIR / f"baseline_{target_col}_test_report.csv", index_col=0)
    week3 = pd.read_csv(RESULTS_DIR / f"improved_{target_col}_test_report.csv", index_col=0)
    week4 = pd.read_csv(RESULTS_DIR / f"week4_{target_col}_test_report.csv", index_col=0)

    combined = pd.DataFrame({
        "baseline_f1": baseline["f1-score"],
        "week3_f1": week3["f1-score"],
        "week4_f1": week4["f1-score"],
    })
    combined["week4_vs_baseline"] = combined["week4_f1"] - combined["baseline_f1"]
    combined["week4_vs_week3"] = combined["week4_f1"] - combined["week3_f1"]

    print(f"\n{'='*80}\n{label} — Baseline vs Week 3 vs Week 4\n{'='*80}")
    print(combined.round(3).to_string())

    combined.round(4).to_csv(RESULTS_DIR / f"comparison_all_{target_col}.csv")
    print(f"Saved -> {RESULTS_DIR / f'comparison_all_{target_col}.csv'}")

    for name, df in [("Baseline", baseline), ("Week 3", week3), ("Week 4", week4)]:
        acc = df.loc["accuracy", "f1-score"]
        macro = df.loc["macro avg", "f1-score"]
        print(f"{name}: accuracy={acc:.3f}, macro F1={macro:.3f}")


if __name__ == "__main__":
    compare("category", "Category")
    compare("urgency", "Urgency")