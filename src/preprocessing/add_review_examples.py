import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

review_comments = [
    "The professor explains every topic in a very clear way.",
    "Lectures were a bit boring but the notes were helpful.",
    "Great course, I learned a lot and enjoyed the practicals.",
    "The teacher is friendly and always answers questions in class.",
    "Easy marks if you attend the lectures and submit on time.",
    "The syllabus is well organised and the slides are easy to follow.",
    "I liked the group project, it was a good way to learn.",
    "The course is quite hard but the lecture notes are very clear.",
    "He speaks quietly, so sit near the front of the class.",
    "Good course overall, the final exam was fair.",
    "The assignments were interesting and related to real examples.",
    "She gives useful feedback on every submission.",
    "Not the most exciting subject, but the teacher makes it bearable.",
    "The textbook is enough to prepare for the exams.",
    "A well structured course with a good balance of theory and practice.",
    "The teacher shows videos and examples which makes classes lively.",
    "I would recommend this course to anyone interested in data.",
    "Lab sessions were useful and the instructor was helpful.",
    "The course content is outdated in a few places but still useful.",
    "Midterm was tricky, the final was easier than expected.",
    "Very knowledgeable professor and a relaxed classroom environment.",
    "The grading is fair and the marks were released on time.",
    "I enjoyed the discussions, everyone got a chance to speak.",
    "The online material is good, you can learn most of it on your own.",
    "Average course, nothing special but nothing bad either.",
    "The instructor is strict about deadlines but very approachable.",
    "Solid introduction to the subject, the examples were helpful.",
    "The class is fun and the quizzes keep you on track.",
    "Please add more practice problems before the exams.",
    "The teaching style is old fashioned but the content is good.",
    "Loved the case studies, they made the topics easy to remember.",
    "The professor is very passionate about the subject.",
    "The attendance policy is strict but the lectures are worth attending.",
    "Interesting topics, and the reading list is well chosen.",
    "Useful course for internships, the tools we learned are in demand.",
    "The projects were challenging in a good way.",
    "Clear explanations and quick replies to emails from the teacher.",
    "The course could use a few more guest lectures.",
    "Enjoyable class, the teacher keeps a good pace.",
    "Everything was explained well and the exam matched the syllabus.",
]

n_train = 28
n_val = 6
parts = {
    "train": review_comments[:n_train],
    "val": review_comments[n_train:n_train + n_val],
    "test": review_comments[n_train + n_val:],
}

for split, comments in parts.items():
    path = DATA_DIR / f"{split}.csv"
    df = pd.read_csv(path, keep_default_na=False)

    if "text" not in df.columns:
        print("No column called 'text' in", path)
        print("Columns found:", list(df.columns))
        raise SystemExit

    already_there = set(df["text"])
    new_rows = []
    for comment in comments:
        if comment in already_there:
            continue
        row = {col: "" for col in df.columns}
        row["text"] = comment
        if "category" in df.columns:
            row["category"] = "No_Concern"
        if "urgency" in df.columns:
            row["urgency"] = "No_Concern"
        if "recommended_action" in df.columns:
            row["recommended_action"] = "No action required"
        new_rows.append(row)

    if "id" in df.columns:
        start = len(df) + 1
        for i, row in enumerate(new_rows):
            row["id"] = f"REV{start + i:04d}"

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        df.to_csv(path, index=False)
    print(split, ": added", len(new_rows), "rows, now", len(df))