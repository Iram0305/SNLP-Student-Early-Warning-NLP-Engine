# Student Early-Warning NLP Engine

**Group 6 — AI University Project** (Roll No. E037, E039, E040, E041, E044)

An NLP component that identifies potentially important student-support signals
(academic, financial, mental-health, harassment/safety, administrative concerns)
from free-text student communications (emails, feedback, help-desk requests),
and outputs a triage recommendation for academic advisors — **advisory only,
never a high-stakes automated decision.**

## Problem

Students often express difficulty — academic, financial, personal, or
safety-related — through everyday text (emails, feedback forms, help-desk
tickets) rather than through a formal complaint channel. These signals are
easy for advisors to miss at scale. This project builds a triage layer that
surfaces and categorizes these signals for human review.

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

**Interface (planned, Week 6):** `POST /analyze-message`

Any other AI University component (e.g. Group 5's Feedback Intelligence, or
Group 4's Knowledge Assistant) can call this module by sending message text
and receiving a structured triage result — no need to read this repo's
internals.

## Current Status (Week 1–2)

- [x] Problem definition & institutional context
- [x] NLP task formulation (two-headed classification: category + urgency)
- [x] Synthetic dataset generated (228 labeled examples, documented below)
- [x] Preprocessing + stratified train/val/test split (70/15/15)
- [x] Baseline model: TF-IDF + Logistic Regression (separate models for
      category and urgency)
- [x] Initial evaluation (precision/recall/F1, confusion matrix — see `results/`)

## Dataset

**Source:** Synthetically generated for this coursework (`src/preprocessing/generate_dataset.py`).
No real student data is used at this stage.

- **Generation method:** template + slot-filling (course-name substitution)
  across 6 categories × up to 3 urgency levels, hand-written by the group to
  reflect realistic phrasing patterns described in the project brief.
- **Size:** 228 unique examples after deduplication
- **Labels:** `category` (Academic difficulty, Financial difficulty,
  Personal/Mental health, Harassment/Safety, Administrative, No_Concern),
  `urgency` (Low, Medium, High, No_Concern)
- **Split:** 70% train / 15% val / 15% test, stratified by category
- **Preprocessing:** whitespace normalization, deduplication
- **Privacy:** N/A at this stage — no real student data involved. If real
  (anonymized) institutional data is incorporated in later weeks, it will be
  documented here along with anonymization method and authorization.
- **Limitation:** synthetic templated data is less lexically diverse than
  real messages; real-world performance is expected to be lower. This will
  be addressed via the improved model (Week 3–4) and error analysis (Week 5),
  and ideally augmented with real (anonymized) or better-varied LLM-generated data.

## Baseline Model

TF-IDF (unigrams + bigrams) → Logistic Regression, trained separately for
`category` and `urgency`, both with `class_weight="balanced"` to handle
class imbalance.

**Test set results** (see `results/` for full reports and confusion matrices):

| Task | Accuracy | Macro F1 |
|------|----------|----------|
| Category | 0.91 | 0.87 |
| Urgency | 0.86 | 0.75 |

These numbers are inflated by the templated nature of the synthetic data and
are expected to drop on more realistic/held-out phrasing — this gap is the
motivation for the improved model in later weeks.

## Repository Structure

```
project/
├── README.md
├── requirements.txt
├── data/                  # raw + train/val/test splits
├── notebooks/
├── src/
│   ├── preprocessing/     # dataset generation, cleaning, splitting
│   ├── models/            # baseline model, saved artifacts
│   ├── evaluation/        # evaluation scripts, metrics
│   └── api/                # (Week 6) reusable API/module interface
├── tests/
├── results/                # evaluation reports, confusion matrices
├── docs/                   # architecture diagram, API docs, eval docs
└── demo/
```

## Responsible AI Note

This system is an **advisory/triage tool only**. It must not be used to make
autonomous, high-stakes decisions about students (e.g. academic penalties,
disciplinary action). All flagged messages require human review by an
academic advisor or appropriate staff before any action is taken.

## How to Reproduce

```bash
pip install -r requirements.txt

# 1. Generate synthetic dataset
cd src/preprocessing
python generate_dataset.py --n_per_class 18 --out ../../data/raw_dataset.csv

# 2. Preprocess + split
python preprocess.py --in ../../data/raw_dataset.csv --out_dir ../../data

# 3. Train + evaluate baseline
cd ../models
python baseline.py
```
