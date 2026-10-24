# Student Early-Warning NLP Engine

**Group 6 — SNLP Course Project 2026 (AI University: Building Reusable NLP Assets)**

| Roll No. | Name |
|----------|------|
| E037 | Iram Shaikh |
| E039 | Kesar Joshi |
| E040 | Kavish Purohit |
| E041 | Meet Patel |
| E044 | Riddhi Bhagat |

An NLP component that identifies potentially important student-support signals
(academic, financial, mental-health, harassment/safety, administrative concerns)
from free-text student communications, and outputs a triage recommendation for
academic advisors — **advisory only, never a high-stakes automated decision.**

---

## Problem

Students express difficulty — academic, financial, personal or safety-related —
through everyday text such as emails, feedback forms and help-desk tickets,
rather than through formal complaint channels. At institutional scale these
signals are easy to miss: genuine distress is buried under routine queries, and
problems are often noticed only after they have escalated.

This project builds a triage layer that surfaces and categorises those signals
so that staff review the important messages first.

---

## Reusable Asset — Input / Output Contract

**Input:** raw student message text (string)

**Output (JSON):**

```json
{
  "input_id": "MSG0001",
  "category": "Academic difficulty",
  "category_confidence": 0.82,
  "urgency": "High",
  "urgency_confidence": 0.79,
  "recommended_action": "Academic advisor follow-up"
}
```

**Categories:** Academic difficulty · Financial difficulty · Personal/Mental health ·
Harassment/Safety · Administrative · No_Concern

**Urgency levels:** High · Medium · Low · No_Concern

---

## Quick Start

```bash
pip install -r requirements.txt

# Python module
cd src/models
python pipeline_v2.py

# HTTP API
cd src/api
uvicorn app:app --reload        # then open http://127.0.0.1:8000/docs

# Demo interface
cd demo
streamlit run "streamlit app.py"
```

---

## API / Module Documentation

### Python module

```python
from pipeline_v2 import analyze_message

result = analyze_message("I cannot afford my hostel fees this month.")
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | str | yes | Raw student message |
| `input_id` | str | no | Your own reference id; auto-generated if omitted |

Returns a dictionary:

| Field | Type | Description |
|-------|------|-------------|
| `input_id` | str | Reference id |
| `category` | str | One of the six categories |
| `category_confidence` | float | 0 to 1 |
| `urgency` | str | High / Medium / Low / No_Concern |
| `urgency_confidence` | float | 0 to 1 |
| `recommended_action` | str | Which office should handle it |

### HTTP API

Start the server:

```bash
cd src/api
uvicorn app:app --reload
```

Interactive documentation: **http://127.0.0.1:8000/docs**

#### `POST /analyze-message`

Analyse a single message.

```json
// request
{"text": "I cannot afford my hostel fees this month."}

// response
{
  "input_id": "MSG0001",
  "category": "Financial difficulty",
  "category_confidence": 0.9,
  "urgency": "High",
  "urgency_confidence": 0.97,
  "recommended_action": "Financial aid office referral"
}
```

#### `POST /analyze-feedback`

Batch endpoint. Returns **only** the items containing support signals.

```json
// request
{
  "items": [
    {"id": "FB001", "text": "the pace was too fast and I may drop out"}
  ],
  "min_confidence": 0.5
}

// response
{
  "received": 1,
  "flagged": 1,
  "signals": [
    {
      "input_id": "FB001",
      "category": "Academic difficulty",
      "category_confidence": 0.87,
      "urgency": "High",
      "urgency_confidence": 0.91,
      "recommended_action": "Academic advisor follow-up"
    }
  ]
}
```

#### `POST /feedback-summary`

Returns category and urgency counts across a batch, plus all high-priority items.
Intended for dashboard use.

#### `GET /`

Health check.

---

## Integration — Group 5 (Student Feedback Intelligence)

Group 5 extracts aspects and sentiment from student feedback. Sentiment alone
does not reveal student-support needs: a comment tagged *"Pace — Negative"* may
also contain a signal that a student is at risk of dropping out. This component
detects those signals.

**Flow:** Group 5 feedback text → Group 6 Early-Warning Engine → flagged support
signals with urgency and recommended action.

Python:

```python
from integration import find_support_signals

feedback = [{"id": "FB001", "text": "the pace was too fast and I may drop out"}]
flagged = find_support_signals(feedback)
```

HTTP: `POST /analyze-feedback` (schema above).

File-based exchange (JSON or CSV, detected from the file extension):

```python
from integration import process_group5_file

process_group5_file(
    "../../data/integration/group5 feedback input.json",
    "../../data/integration/group5 triage output.json"
)
```

A runnable demonstration is in `demo/group5 integration demo.py`. It uses the
Group 5 file when present and falls back to built-in sample feedback otherwise.

---

## Architecture

See `docs/architecture.png`.