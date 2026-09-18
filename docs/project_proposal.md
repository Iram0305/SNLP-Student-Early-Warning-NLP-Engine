# Project Proposal — Student Early-Warning NLP Engine

**Group 6** | Roll No. E037, E039, E040, E041, E044

## Problem
Students frequently express academic, financial, personal, or safety-related
difficulties through routine textual interactions — emails, feedback forms,
help-desk requests — rather than formal complaint channels. At institutional
scale, these signals are easy for advisors and support staff to miss, meaning
students who need help often go unnoticed until problems escalate.

## Institutional Users
Academic advisors, student support/counselling staff, and administrative
offices responsible for student welfare. The system is a **triage aid**, not
a decision-maker — final judgment and action remain with human staff.

## Input
Free-text student message (email, feedback, help-desk ticket, or similar).

*Example:* "I have missed several classes because of difficulties at home and
I am worried that I may not be able to complete the course."

## Output
Structured JSON triage result:
```json
{
  "category": "Academic difficulty",
  "urgency": "High",
  "recommended_action": "Academic advisor follow-up",
  "confidence": 0.82
}
```

## NLP Task Formulation
Two parallel classification sub-tasks operating on the same input text:
1. **Category classification** (multi-class): Academic difficulty, Financial
   difficulty, Personal/Mental health, Harassment/Safety, Administrative,
   No_Concern
2. **Urgency classification** (ordinal-ish multi-class): Low, Medium, High,
   No_Concern

Modeled as two independent classification heads (rather than one joint label
space) for simplicity and interpretability at the baseline stage. Later
stretch work may explore information extraction (key-phrase highlighting) and
clustering of emerging concern types for the dashboard stretch goal.

## Dataset
No pre-existing public dataset matches this exact task. We generated a
**synthetic dataset** (228 labeled examples after deduplication) via
template + slot-filling covering all category/urgency combinations, designed
to reflect realistic phrasing patterns from the project brief. Documented
fully in the repository README, including generation method and known
limitations (lower lexical diversity than real text). Real (anonymized)
institutional data may be incorporated in later weeks, subject to privacy
and authorization constraints per the course guidelines.

## Proposed Approach
- **Baseline (Week 1–2):** TF-IDF (unigram+bigram) features + Logistic
  Regression, trained separately for category and urgency, with class
  balancing to handle skewed label distribution.
- **Improved approach (Week 3–4):** Sentence-transformer embeddings (e.g.
  `all-MiniLM-L6-v2`) with a classifier head, and/or an LLM-based
  zero/few-shot classifier for comparison — explicitly benchmarked against
  the TF-IDF baseline rather than used as a standalone black box.
- **Evaluation:** Precision, recall, F1 (macro, due to class imbalance),
  confusion matrix, and false-positive analysis (critical given the
  advisory/triage nature of the system — false positives waste advisor time,
  false negatives risk missing a genuine student in need).

## Expected Institutional Value
Gives academic advisors and student support staff an automated first-pass
signal across large volumes of routine text, surfacing potentially important
concerns that would otherwise require manual reading of every message. Framed
explicitly as an advisory/triage layer with mandatory human oversight,
consistent with responsible-AI requirements for any system touching
sensitive student welfare information.
