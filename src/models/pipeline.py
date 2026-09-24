"""
Version 1 of the NLP pipeline for the Student Early-Warning NLP Engine.

Wraps the Week 3 improved model (sentence embeddings + Logistic Regression)
into a single callable matching the input/output contract documented in
the project README, so other groups can call this module directly.

Usage:
    from pipeline import analyze_message
    result = analyze_message("I haven't paid my fees and might be removed from the rolls.")
    print(result)
"""

import joblib
from pathlib import Path
from sentence_transformers import SentenceTransformer

MODELS_DIR = Path(__file__).resolve().parent / "saved"
MODEL_NAME = "all-MiniLM-L6-v2"

RECOMMENDED_ACTION = {
    "Academic difficulty": "Academic advisor follow-up",
    "Financial difficulty": "Financial aid office referral",
    "Personal/Mental health": "Counselling services referral",
    "Administrative": "Route to administrative office",
    "Harassment/Safety": "Escalate to student safety/conduct office",
    "No_Concern": "No action required",
}

_embedder = None
_category_clf = None
_urgency_clf = None
_msg_counter = 0


def _load_models():
    global _embedder, _category_clf, _urgency_clf
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_NAME)
    if _category_clf is None:
        _category_clf = joblib.load(MODELS_DIR / "improved_category.joblib")
    if _urgency_clf is None:
        _urgency_clf = joblib.load(MODELS_DIR / "improved_urgency.joblib")


def analyze_message(text: str, input_id: str = None) -> dict:
    """
    Takes raw student message text, returns the structured triage JSON
    described in the README's Reusable Asset contract.
    """
    global _msg_counter
    _load_models()

    if input_id is None:
        _msg_counter += 1
        input_id = f"MSG{_msg_counter:04d}"

    vector = _embedder.encode([text], convert_to_numpy=True)

    category_pred = _category_clf.predict(vector)[0]
    category_proba = _category_clf.predict_proba(vector)[0].max()

    urgency_pred = _urgency_clf.predict(vector)[0]
    urgency_proba = _urgency_clf.predict_proba(vector)[0].max()

    return {
        "input_id": input_id,
        "category": category_pred,
        "category_confidence": round(float(category_proba), 2),
        "urgency": urgency_pred,
        "urgency_confidence": round(float(urgency_proba), 2),
        "recommended_action": RECOMMENDED_ACTION.get(category_pred, "Route for manual review"),
    }


if __name__ == "__main__":
    sample_messages = [
        "I have not been able to pay my tuition fees this semester and I am worried I'll be removed from the rolls.",
        "Could you share the slides from today's Machine Learning lecture?",
        "I've been feeling extremely overwhelmed and hopeless lately and I don't know who to talk to.",
    ]

    for msg in sample_messages:
        result = analyze_message(msg)
        print(result)