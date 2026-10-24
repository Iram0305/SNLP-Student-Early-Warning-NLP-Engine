import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src" / "api"))

from integration import find_support_signals, summarise_signals, load_feedback_file

GROUP5_FILE = Path(__file__).resolve().parents[1] / "data" / "integration" / "group5 feedback input.json"

sample_feedback = [
    {"id": "FB001", "text": "The lectures were very informative but the pace was too fast."},
    {"id": "FB002", "text": "Assignments were difficult but the examples helped a lot."},
    {"id": "FB003", "text": "The pace was too fast and I have fallen so far behind that I am thinking of dropping out."},
    {"id": "FB004", "text": "Great teaching, really enjoyed the practical sessions."},
    {"id": "FB005", "text": "I could not afford the lab materials this semester so I missed several practicals."},
    {"id": "FB006", "text": "The workload has left me completely burnt out and I cannot cope anymore."},
    {"id": "FB007", "text": "Course content was well structured, thank you."},
    {"id": "FB008", "text": "A classmate in my project group has been making uncomfortable comments about me."},
]

if GROUP5_FILE.exists():
    feedback = load_feedback_file(GROUP5_FILE)
    source = f"Group 5 file ({GROUP5_FILE.name})"
else:
    feedback = sample_feedback
    source = "built-in sample data (Group 5 file not found)"

print("=" * 70)
print("GROUP 5 -> GROUP 6 INTEGRATION DEMO")
print("=" * 70)
print(f"\nSource: {source}")
print(f"Group 5 collected {len(feedback)} feedback comments.")
print("Passing them to the Group 6 Early-Warning Engine...\n")

flagged = find_support_signals(feedback)

print(f"Support signals detected: {len(flagged)} of {len(feedback)}\n")
print("-" * 70)

for signal in flagged:
    print(f"ID       : {signal['input_id']}")
    print(f"Category : {signal['category']}  ({signal['category_confidence']})")
    print(f"Urgency  : {signal['urgency']}  ({signal['urgency_confidence']})")
    print(f"Action   : {signal['recommended_action']}")
    print("-" * 70)

print("\nSUMMARY FOR DASHBOARD")
summary = summarise_signals(feedback)
print(f"Total analysed      : {summary['total_analysed']}")
print(f"High priority cases : {summary['high_priority_count']}")
print(f"Category breakdown  : {summary['category_breakdown']}")
print(f"Urgency breakdown   : {summary['urgency_breakdown']}")