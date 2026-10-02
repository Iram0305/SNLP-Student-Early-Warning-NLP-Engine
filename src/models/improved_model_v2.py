import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, f1_score

EMBED_DIR = Path(__file__).resolve().parent / "embeddings_v2"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
MODELS_DIR = Path(__file__).resolve().parent / "saved"
MODELS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


def load_split(split_name):
    X = np.load(EMBED_DIR / f"{split_name}_embeddings.npy")
    y_df = pd.read_csv(EMBED_DIR / f"{split_name}_labels.csv", keep_default_na=False)
    return X, y_df


def pick_best_classifier(X_train, y_train, X_val, y_val, label):
    candidates = {
        "logreg": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        "svm": SVC(kernel="linear", class_weight="balanced", probability=True, random_state=42),
    }

    print(f"\n--- Choosing classifier for {label} on validation set ---")
    best_name, best_model, best_f1 = None, None, -1

    for name, clf in candidates.items():
        clf.fit(X_train, y_train)
        preds = clf.predict(X_val)
        macro_f1 = f1_score(y_val, preds, average="macro", zero_division=0)
        print(f"{name}: macro F1 = {macro_f1:.3f}")

        if macro_f1 > best_f1:
            best_name, best_model, best_f1 = name, clf, macro_f1

    print(f"Selected: {best_name} (macro F1 = {best_f1:.3f})")
    return best_name, best_model


def train_and_evaluate(target_col, label):
    X_train, train_df = load_split("train")
    X_val, val_df = load_split("val")
    X_test, test_df = load_split("test")

    y_train = train_df[target_col]
    y_val = val_df[target_col]
    y_test = test_df[target_col]

    best_name, clf = pick_best_classifier(X_train, y_train, X_val, y_val, label)

    print(f"\n{'='*60}\nWEEK 4 MODEL (mpnet embeddings + {best_name}) — {label}\n{'='*60}")

    preds = clf.predict(X_test)
    report = classification_report(y_test, preds, zero_division=0)
    print(report)

    report_dict = classification_report(y_test, preds, zero_division=0, output_dict=True)
    cm = confusion_matrix(y_test, preds, labels=sorted(y_test.unique()))
    cm_df = pd.DataFrame(cm, index=sorted(y_test.unique()), columns=sorted(y_test.unique()))

    pd.DataFrame(report_dict).transpose().to_csv(RESULTS_DIR / f"week4_{target_col}_test_report.csv")
    cm_df.to_csv(RESULTS_DIR / f"week4_{target_col}_confusion_matrix.csv")

    joblib.dump(clf, MODELS_DIR / f"week4_{target_col}.joblib")
    print(f"Saved model -> {MODELS_DIR / f'week4_{target_col}.joblib'}")

    return clf


if __name__ == "__main__":
    train_and_evaluate("category", "Category")
    train_and_evaluate("urgency", "Urgency")