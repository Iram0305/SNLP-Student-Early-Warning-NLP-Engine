"""
Synthetic dataset generator for the Student Early-Warning NLP Engine.

Generates labeled student messages (emails / feedback / help-desk text) across:
  - category: Academic difficulty, Financial difficulty, Personal/Mental health,
              Administrative, Harassment/Safety, None (neutral/no concern)
  - urgency: Low, Medium, High, None (for neutral messages)

This is SYNTHETIC data built from templates + slot-filling + paraphrase variation,
generated for coursework purposes to bootstrap a baseline model in Week 1-2.
No real student data is used. Document this generation approach in your report
(per Section 20 of the handout: model/tool, purpose, prompts, limitations).

Usage:
    python generate_dataset.py --n_per_class 45 --out ../../data/raw_dataset.csv
"""

import argparse
import csv
import random

random.seed(42)

# ---------------------------------------------------------------------------
# Template bank: (category, urgency, list of message templates)
# {name} slots are filled for light lexical variety; not essential to meaning.
# ---------------------------------------------------------------------------

TEMPLATES = {
    ("Academic difficulty", "High"): [
        "I have missed several classes because of difficulties at home and I am worried that I may not be able to complete the course.",
        "I have fallen so far behind in {course} that I don't think I can catch up before the exam.",
        "I've missed the last three weeks of {course} due to a family emergency and I'm at risk of failing.",
        "I don't understand anything that has been taught in {course} this semester and the mid-terms are next week.",
        "I am on the verge of dropping out because I cannot keep up with the coursework anymore.",
        "My attendance has dropped below the required percentage and I'm scared I'll be barred from the exam.",
        "I've failed two internal assessments in a row and I don't know what to do next.",
    ],
    ("Academic difficulty", "Medium"): [
        "I'm struggling to understand the concepts covered in {course} over the last two weeks.",
        "I missed a couple of lectures in {course} and I'm finding it hard to catch up on my own.",
        "The pace of {course} has been too fast for me and I'm falling behind on assignments.",
        "I did poorly on my last assignment in {course} and I'm not sure how to improve.",
        "I'm having trouble balancing coursework across {course} and my other subjects this semester.",
        "I need some extra guidance on the topics from last week's {course} lecture.",
    ],
    ("Academic difficulty", "Low"): [
        "Could you clarify the deadline extension policy for {course} assignments?",
        "I had a small doubt about the grading rubric used for the {course} project.",
        "Is there a recommended textbook for {course} that covers the topics in more depth?",
        "I'd like some feedback on my last submission for {course} when you have time.",
    ],
    ("Financial difficulty", "High"): [
        "I have not been able to pay my tuition fees this semester and I am worried I'll be removed from the rolls.",
        "My family's financial situation has worsened and I may have to drop out due to unpaid fees.",
        "I lost my scholarship and I don't know how I'll continue paying for {course} materials and tuition.",
        "I'm unable to afford the hostel fees this month and I don't know who to contact for support.",
        "My father lost his job recently and we can no longer manage the tuition payments for this semester.",
        "I'm at risk of being deregistered from {course} because of overdue fee payments and I need urgent help.",
        "I can't afford the lab equipment required for {course} and my deadline to submit is this week.",
    ],
    ("Financial difficulty", "Medium"): [
        "I'm having some difficulty managing my fee payments this semester and wanted to ask about installment options.",
        "Could you tell me if there are any scholarship or financial aid options available for students like me?",
        "I'm a bit behind on my fee payment and want to know the process for requesting an extension.",
        "Managing both hostel and {course} material costs this month has been tight, are there any aid options?",
        "I wanted to ask about part-time work opportunities on campus to help cover my {course} related expenses.",
    ],
    ("Financial difficulty", "Low"): [
        "Could you share the fee payment deadlines for this semester?",
        "I wanted to check the refund policy in case I withdraw from an elective.",
        "Is there a fee breakdown available for {course} materials and lab charges?",
        "Could you clarify if the scholarship renewal requires a fresh application every year?",
    ],
    ("Personal/Mental health", "High"): [
        "I've been feeling extremely overwhelmed and hopeless lately and I don't know who to talk to.",
        "I haven't been able to sleep or eat properly for days because of the stress I'm under.",
        "I feel like I can't cope anymore with everything going on and I need to speak to someone urgently.",
        "The anxiety around my exams has become unbearable and it's affecting every part of my life.",
        "I've been isolating myself from everyone and I don't see the point in continuing like this.",
        "I'm going through a personal crisis at home and it's become too much to handle alone.",
        "I feel completely burnt out and don't know how much longer I can keep pushing through {course}.",
    ],
    ("Personal/Mental health", "Medium"): [
        "I've been feeling quite stressed and low on energy for the past couple of weeks.",
        "I'm finding it hard to stay motivated and focused on my studies lately.",
        "I've been going through a difficult personal situation that's affecting my concentration in class.",
        "I feel anxious before every {course} exam and it's starting to affect my performance.",
        "I've been feeling quite disconnected from my classmates and struggling to keep up with {course}.",
        "The workload this semester has left me feeling constantly drained and a bit low.",
    ],
    ("Personal/Mental health", "Low"): [
        "I've been a little tired lately, is there a wellness session or counselling drop-in I could attend?",
        "Could you point me to resources on managing exam stress?",
        "I'd like to know more about the peer support groups available on campus.",
        "Are there any mindfulness or stress-management workshops planned this semester?",
    ],
    ("Administrative", "Medium"): [
        "I need to update my address on record but I'm not sure which office to contact.",
        "My transcript has an error in my {course} grade and I need it corrected before applications close.",
        "I haven't received my hall ticket for the upcoming exams, can someone look into this?",
        "I need to request a leave of absence for {course} due to a family function next week.",
    ],
    ("Administrative", "Low"): [
        "Could you tell me the process for requesting a bonafide certificate?",
        "I wanted to confirm the last date for course registration this semester.",
        "How do I apply for a duplicate ID card?",
        "Can you share the academic calendar for this semester?",
        "Could you tell me which office handles hostel room change requests?",
        "I wanted to know the process for adding a minor elective alongside {course}.",
    ],
    ("Harassment/Safety", "High"): [
        "A senior student has been repeatedly harassing me online and I don't feel safe on campus anymore.",
        "I'm being bullied by classmates in my {course} group and it has gotten worse over the past week.",
        "Someone has been sending me threatening messages and I don't know who to report it to.",
        "I witnessed a faculty member behaving inappropriately toward a student and want to report it confidentially.",
        "I've been followed and cornered by the same student twice this week and I'm genuinely scared.",
        "Explicit messages are being circulated about me in a {course} class group and I need this addressed urgently.",
        "I reported an incident last week and nothing has been done, the harassment has continued in {course}.",
    ],
    ("Harassment/Safety", "Medium"): [
        "A few students in {course} have been making uncomfortable comments about me in the group chat.",
        "I feel excluded and targeted by a group of classmates and it's affecting my ability to attend class.",
        "Someone in my {course} batch keeps making jokes at my expense and it's starting to bother me.",
        "I've noticed repeated unwelcome comments about my appearance from a classmate in {course}.",
        "A group project teammate has been dismissive and disrespectful toward me throughout {course}.",
    ],
    ("No_Concern", "No_Concern"): [
        "Thank you for the extra reading material shared after the {course} lecture, it was really helpful.",
        "The {course} project guidelines were very clear, thanks for the detailed rubric.",
        "Just wanted to say I really enjoyed this week's session on {course}.",
        "Could you share the slides from today's {course} lecture?",
        "What time does the {course} lab session start tomorrow?",
        "Looking forward to the guest lecture on {course} next week!",
        "The workshop on {course} last week was excellent, thank you for organizing it.",
        "Is the {course} field trip still happening next month?",
        "Congratulations to the team for winning the hackathon, great work!",
        "Could you confirm the room number for tomorrow's {course} tutorial?",
        "Really appreciated the extra office hours for {course} this week.",
        "Is there a recording available for the {course} session I missed due to a clash?",
        "The new {course} assignment format is much clearer than before, thanks!",
        "Can you share the reading list for next month's {course} topics?",
        "The {course} study group has been really helpful, thanks for setting it up.",
    ],
}

COURSES = [
    "Machine Learning", "Natural Language Processing", "Data Structures",
    "Operating Systems", "Statistics", "Database Systems", "Linear Algebra",
    "Software Engineering", "Computer Networks", "Data Science",
]

RECOMMENDED_ACTION = {
    "Academic difficulty": "Academic advisor follow-up",
    "Financial difficulty": "Financial aid office referral",
    "Personal/Mental health": "Counselling services referral",
    "Administrative": "Route to administrative office",
    "Harassment/Safety": "Escalate to student safety/conduct office",
    "No_Concern": "No action required",
}


def fill_slots(template: str) -> str:
    if "{course}" in template:
        return template.format(course=random.choice(COURSES))
    return template


def generate(n_per_class: int, out_path: str):
    rows = []
    idx = 1
    for (category, urgency), templates in TEMPLATES.items():
        # generate n_per_class UNIQUE texts per group by combining template
        # cycling with course-slot variation; skip exact repeats
        seen = set()
        attempts = 0
        count = 0
        while count < n_per_class and attempts < n_per_class * 20:
            attempts += 1
            template = templates[attempts % len(templates)]
            text = fill_slots(template)
            if text in seen:
                continue
            seen.add(text)
            rows.append({
                "id": f"MSG{idx:04d}",
                "text": text,
                "category": category,
                "urgency": urgency,
                "recommended_action": RECOMMENDED_ACTION[category],
            })
            idx += 1
            count += 1
        if count < n_per_class:
            print(f"WARNING: only generated {count}/{n_per_class} unique examples for "
                  f"({category}, {urgency}) - template bank too small at this slot diversity.")

    random.shuffle(rows)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "category", "urgency", "recommended_action"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} examples -> {out_path}")
    # class distribution summary
    from collections import Counter
    cat_counts = Counter(r["category"] for r in rows)
    urg_counts = Counter(r["urgency"] for r in rows)
    print("Category distribution:", dict(cat_counts))
    print("Urgency distribution:", dict(urg_counts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_per_class", type=int, default=20,
                         help="Number of examples to generate per (category, urgency) template group")
    parser.add_argument("--out", type=str, default="../../data/raw_dataset.csv")
    args = parser.parse_args()
    generate(args.n_per_class, args.out)
