"""
Local web app for the Student Early-Warning NLP Engine.

Serves the single-page UI in webapp/static/ and a small JSON API on top of
the Week 4 pipeline (src/models/pipeline_v2.py, MPNet + classifier).

Run from the repo root:
    python webapp/server.py
then open http://127.0.0.1:8765 (or double-click start_app.bat)
"""

import csv
import json
import os
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
sys.path.insert(0, str(ROOT / "src" / "models"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from code_guide import CODE_FILES, build_annotations

HOST = "127.0.0.1"
PORT = int(os.environ.get("EWS_PORT", "8765"))
PID_FILE = Path(__file__).resolve().parent / "server.pid"

NOT_SUPPORT = ["No_Concern", "Administrative"]
SUPPORT_THRESHOLD = 0.5

CATEGORY_GUIDANCE = {
    "Academic difficulty": "The student is reporting difficulty keeping up with coursework. Early contact from an academic advisor is usually the most effective step: a catch-up plan, reviewed deadlines or peer tutoring.",
    "Financial difficulty": "The student is reporting financial pressure that may affect their enrolment. The financial aid office can advise on instalment plans, hardship funds and scholarships. These cases tend to escalate quickly if left unaddressed.",
    "Personal/Mental health": "The student is describing personal or emotional difficulty. Route to counselling services, respond promptly, and avoid asking the student to repeat their disclosure to multiple staff members.",
    "Harassment/Safety": "The student is reporting a safety or harassment concern. Escalate to the student safety or conduct office and follow the formal reporting procedure. Handle with strict confidentiality.",
    "Administrative": "This is a process or records request rather than a welfare concern. Route it to the relevant administrative office.",
    "No_Concern": "No support concern was detected. This looks like routine correspondence and does not need advisor follow-up.",
}

URGENCY_GUIDANCE = {
    "High": "Suggested response time: within 24 hours.",
    "Medium": "Suggested response time: within the current week.",
    "Low": "Can be handled through normal correspondence.",
    "No_Concern": "No follow-up required.",
}

# Model loading takes 10-30 s, so it happens in a background thread and the
# UI polls /api/status until it is ready.
_state = {"ready": False, "error": None, "loaded_in": None}
_analyze = None


def _warm_up():
    global _analyze
    start = time.time()
    try:
        from pipeline_v2 import analyze_message
        analyze_message("warm-up message", input_id="WARMUP")
        _analyze = analyze_message
        _state["ready"] = True
        _state["loaded_in"] = round(time.time() - start, 1)
    except Exception as exc:  # shown in the UI instead of crashing the server
        _state["error"] = f"{type(exc).__name__}: {exc}"


def _require_model():
    if _state["error"]:
        raise HTTPException(500, f"Model failed to load: {_state['error']}")
    if not _state["ready"]:
        raise HTTPException(503, "Model is still loading, try again in a few seconds.")


@asynccontextmanager
async def lifespan(_app):
    PID_FILE.write_text(str(os.getpid()))
    threading.Thread(target=_warm_up, daemon=True).start()
    yield
    PID_FILE.unlink(missing_ok=True)


app = FastAPI(title="Student Early-Warning NLP Engine (local web app)", version="2.0", lifespan=lifespan)


class Message(BaseModel):
    text: str
    input_id: Optional[str] = None


class Item(BaseModel):
    id: Optional[str] = None
    text: str


class Batch(BaseModel):
    items: List[Item]


@app.get("/api/status")
def status():
    return {**_state, "model": "all-mpnet-base-v2 + week4 classifiers"}


@app.post("/api/analyze")
def analyze(msg: Message):
    if not msg.text.strip():
        raise HTTPException(400, "Message is empty.")
    _require_model()
    start = time.time()
    result = _analyze(msg.text, input_id=msg.input_id)
    result["guidance"] = CATEGORY_GUIDANCE.get(result["category"], "Route for manual review.")
    result["timing"] = URGENCY_GUIDANCE.get(result["urgency"], "")
    result["needs_review"] = min(result["category_confidence"], result["urgency_confidence"]) < SUPPORT_THRESHOLD
    result["elapsed_ms"] = round((time.time() - start) * 1000)
    return result


@app.post("/api/batch")
def batch(req: Batch):
    _require_model()
    results = []
    for n, item in enumerate(req.items, start=1):
        if not item.text.strip():
            continue
        out = _analyze(item.text, input_id=item.id or f"ITEM{n:03d}")
        out["text"] = item.text
        out["support_signal"] = (out["category"] not in NOT_SUPPORT
                                 and out["category_confidence"] >= SUPPORT_THRESHOLD)
        results.append(out)

    def count(key):
        counts = {}
        for r in results:
            counts[r[key]] = counts.get(r[key], 0) + 1
        return counts

    flagged = [r for r in results if r["support_signal"]]
    return {
        "summary": {
            "total": len(results),
            "support_signals": len(flagged),
            "high_urgency": len([r for r in flagged if r["urgency"] == "High"]),
            "low_confidence": len([r for r in results if r["category_confidence"] < SUPPORT_THRESHOLD]),
        },
        "category_counts": count("category"),
        "urgency_counts": count("urgency"),
        "results": results,
    }


@app.get("/api/sample-batch")
def sample_batch():
    path = ROOT / "data" / "integration" / "group5 feedback input.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_csv(name):
    path = ROOT / "results" / name
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


@app.get("/api/results")
def results():
    return {
        "category": _read_csv("comparison_all_category.csv"),
        "urgency": _read_csv("comparison_all_urgency.csv"),
        "week4_category_report": _read_csv("week4_category_test_report.csv"),
        "week4_urgency_report": _read_csv("week4_urgency_test_report.csv"),
    }


@app.get("/api/dataset")
def dataset():
    out = {}
    for split in ["train", "val", "test"]:
        path = ROOT / "data" / f"{split}.csv"
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        cats = {}
        for r in rows:
            cats[r["category"]] = cats.get(r["category"], 0) + 1
        out[split] = {"rows": len(rows), "categories": cats}
    return out


@app.get("/api/code")
def code_list():
    return [
        {k: f[k] for k in ("path", "group", "title", "summary")}
        for f in CODE_FILES if (ROOT / f["path"]).exists()
    ]


@app.get("/api/code/file")
def code_file(path: str):
    entry = next((f for f in CODE_FILES if f["path"] == path), None)
    if entry is None or not (ROOT / path).exists():
        raise HTTPException(404, "File is not in the code guide.")
    source = (ROOT / path).read_text(encoding="utf-8")
    return {
        "path": path,
        "title": entry["title"],
        "summary": entry["summary"],
        "source": source,
        "annotations": build_annotations(source, entry.get("parts", [])),
    }


@app.post("/api/shutdown")
def shutdown():
    def stop():
        time.sleep(0.8)  # let the HTTP response reach the browser first
        PID_FILE.unlink(missing_ok=True)
        os._exit(0)
    threading.Thread(target=stop, daemon=True).start()
    return {"status": "shutting down"}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    print(f"Student Early-Warning Engine running at http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
