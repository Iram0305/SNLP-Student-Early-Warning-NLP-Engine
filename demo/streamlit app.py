import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src" / "models"))

import streamlit as st
from pipeline_v2 import analyze_message

st.set_page_config(page_title="Student Early-Warning Engine", layout="centered")

st.title("Student Early-Warning NLP Engine")
st.caption("Group 6 - advisory triage for student support messages")

st.warning("This is an advisory tool only. It does not make decisions about students. All flagged messages require review by a staff member.")

examples = {
    "-- type your own --": "",
    "Financial distress": "I have not been able to pay my tuition fees this semester and I am worried I will be removed from the rolls.",
    "Routine question": "Could you share the slides from today's Machine Learning lecture?",
    "Mental health": "I have been feeling extremely overwhelmed and hopeless lately and I don't know who to talk to.",
    "Harassment": "A senior student has been repeatedly harassing me online and I don't feel safe on campus anymore.",
}

choice = st.selectbox("Try an example", list(examples.keys()))
message = st.text_area("Student message", value=examples[choice], height=130)

if st.button("Analyse", type="primary"):
    if not message.strip():
        st.error("Please enter a message.")
    else:
        with st.spinner("Analysing..."):
            result = analyze_message(message)

        st.subheader("Triage result")

        left, right = st.columns(2)
        left.metric("Category", result["category"])
        left.caption(f"Confidence {result['category_confidence']}")
        right.metric("Urgency", result["urgency"])
        right.caption(f"Confidence {result['urgency_confidence']}")

        st.info(f"Recommended action: {result['recommended_action']}")

        lowest = min(result["category_confidence"], result["urgency_confidence"])
        if lowest < 0.5:
            st.error("Low confidence - this message should be read manually.")

        with st.expander("Raw JSON output"):
            st.json(result)