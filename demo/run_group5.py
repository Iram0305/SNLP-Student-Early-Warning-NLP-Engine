import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src" / "models"))

try:
    from src.models.pipeline_v2 import analyze_message
except ImportError:
    from pipeline_v2 import analyze_message

INPUT_FILE = ROOT / "data" / "integration" / "group5 feedback input.json"
OUTPUT_FILE = ROOT / "data" / "integration" / "group5 triage output.json"

CATEGORIES = [
    "Academic difficulty",
    "Financial difficulty",
    "Personal/Mental health",
    "Harassment/Safety",
    "Administrative",
    "No_Concern",
]
URGENCY_LEVELS = ["High", "Medium", "Low", "No_Concern"]
NOT_SUPPORT = ["No_Concern", "Administrative"]


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for item in data["items"]:
        out = analyze_message(item["text"], input_id=item["id"])
        results.append({
            "id": item["id"],
            "category": out["category"],
            "category_confidence": round(out["category_confidence"], 3),
            "urgency": out["urgency"],
            "urgency_confidence": round(out["urgency_confidence"], 3),
            "recommended_action": out["recommended_action"],
        })

    flagged = [r for r in results
               if r["category"] not in NOT_SUPPORT and r["category_confidence"] >= 0.5]

    reply = {
        "from": "Group 6, Student Early-Warning NLP Engine",
        "model_version": "mpnet-week4",
        "advisory_only": True,
        "categories": CATEGORIES,
        "urgency_levels": URGENCY_LEVELS,
        "confidence_range": "0.0 to 1.0 = probability the model gives its chosen label; below 0.5 means low confidence",
        "summary": {
            "total": len(results),
            "support_signals": len(flagged),
            "high_urgency": len([r for r in flagged if r["urgency"] == "High"]),
        },
        "results": results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(reply, f, indent=2, ensure_ascii=False)

    print("Read", len(results), "comments")
    print("Support signals:", len(flagged), "| High urgency:", reply["summary"]["high_urgency"])
    print()
    for r in results:
        print(r["id"], "|", r["category"], f"({r['category_confidence']})", "|", r["urgency"], f"({r['urgency_confidence']})")
    print()
    print("Saved to", OUTPUT_FILE)


main()
