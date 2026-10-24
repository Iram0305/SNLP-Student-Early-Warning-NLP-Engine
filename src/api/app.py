import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "models"))

from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

from pipeline_v2 import analyze_message
from integration import find_support_signals, summarise_signals

app = FastAPI(title="Student Early-Warning NLP Engine", version="1.0")


class SingleMessage(BaseModel):
    text: str
    input_id: Optional[str] = None


class FeedbackItem(BaseModel):
    id: Optional[str] = None
    text: str


class FeedbackBatch(BaseModel):
    items: List[FeedbackItem]
    min_confidence: float = 0.5


@app.get("/")
def health():
    return {"status": "running", "service": "Student Early-Warning NLP Engine"}


@app.post("/analyze-message")
def analyze_single(request: SingleMessage):
    return analyze_message(request.text, input_id=request.input_id)


@app.post("/analyze-feedback")
def analyze_feedback(request: FeedbackBatch):
    items = [item.dict() for item in request.items]
    flagged = find_support_signals(items, request.min_confidence)
    return {
        "received": len(items),
        "flagged": len(flagged),
        "signals": flagged,
    }


@app.post("/feedback-summary")
def feedback_summary(request: FeedbackBatch):
    items = [item.dict() for item in request.items]
    return summarise_signals(items)