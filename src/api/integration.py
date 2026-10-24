import sys
import csv
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "models"))

from pipeline_v2 import analyze_message


def analyze_feedback_batch(feedback_items):
    results = []
    for item in feedback_items:
        if isinstance(item, str):
            text = item
            item_id = None
        else:
            text = item.get("text", "")
            item_id = item.get("id")

        if not text.strip():
            continue

        results.append(analyze_message(text, input_id=item_id))
    return results


def find_support_signals(feedback_items, min_confidence=0.5):
    everything = analyze_feedback_batch(feedback_items)
    flagged = []
    for result in everything:
        is_concern = result["category"] != "No_Concern"
        is_confident = result["category_confidence"] >= min_confidence
        if is_concern and is_confident:
            flagged.append(result)
    return flagged


def summarise_signals(feedback_items):
    everything = analyze_feedback_batch(feedback_items)

    category_counts = {}
    urgency_counts = {}
    for result in everything:
        cat = result["category"]
        urg = result["urgency"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        urgency_counts[urg] = urgency_counts.get(urg, 0) + 1

    high_priority = [r for r in everything if r["urgency"] == "High"]

    return {
        "total_analysed": len(everything),
        "category_breakdown": category_counts,
        "urgency_breakdown": urgency_counts,
        "high_priority_count": len(high_priority),
        "high_priority_items": high_priority,
    }


def load_feedback_file(path):
    path = Path(path)

    if path.suffix.lower() == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("items") or data.get("feedback") or []
        return data

    items = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text") or row.get("feedback") or row.get("comment") or ""
            item_id = row.get("id") or row.get("feedback_id")
            items.append({"id": item_id, "text": text})
    return items


def save_triage_results(results, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        return

    fields = ["input_id", "category", "category_confidence",
              "urgency", "urgency_confidence", "recommended_action"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)


def process_group5_file(input_path, output_path, flagged_only=True):
    items = load_feedback_file(input_path)

    if flagged_only:
        results = find_support_signals(items)
    else:
        results = analyze_feedback_batch(items)

    save_triage_results(results, output_path)

    print(f"Read {len(items)} feedback items from {input_path}")
    print(f"Support signals found: {len(results)}")
    print(f"Written to {output_path}")
    return results