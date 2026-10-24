from pathlib import Path

import joblib
import streamlit as st
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "src" / "models" / "saved"

USE_LIGHT_MODEL = True

if USE_LIGHT_MODEL:
    EMBED_MODEL = "all-MiniLM-L6-v2"
    CATEGORY_FILE = "improved_category.joblib"
    URGENCY_FILE = "improved_urgency.joblib"
    MODEL_LABEL = "MiniLM sentence embeddings"
else:
    EMBED_MODEL = "all-mpnet-base-v2"
    CATEGORY_FILE = "week4_category.joblib"
    URGENCY_FILE = "week4_urgency.joblib"
    MODEL_LABEL = "MPNet sentence embeddings"

RECOMMENDED_ACTION = {
    "Academic difficulty": "Academic advisor follow-up",
    "Financial difficulty": "Financial aid office referral",
    "Personal/Mental health": "Counselling services referral",
    "Administrative": "Route to administrative office",
    "Harassment/Safety": "Escalate to student safety/conduct office",
    "No_Concern": "No action required",
}

CATEGORY_GUIDANCE = {
    "Academic difficulty": "The student is reporting difficulty keeping up with coursework. Early contact from an academic advisor is usually the most effective step. Typical options include agreeing a catch-up plan, reviewing deadlines, or arranging peer tutoring.",
    "Financial difficulty": "The student is reporting financial pressure that may affect their continued enrolment. The financial aid office can advise on instalment plans, hardship funds and scholarship eligibility. Cases in this category tend to escalate quickly if left unaddressed.",
    "Personal/Mental health": "The student is describing personal or emotional difficulty. Route this to counselling services. Respond promptly, and avoid asking the student to repeat their disclosure to multiple staff members.",
    "Harassment/Safety": "The student is reporting a safety or harassment concern. Escalate to the student safety or conduct office and follow the institution's formal reporting procedure. Handle with strict confidentiality.",
    "Administrative": "This is a process or records request rather than a welfare concern. Route it to the relevant administrative office for action.",
    "No_Concern": "No support concern was detected. This appears to be routine correspondence and does not require advisor follow-up.",
}

URGENCY_GUIDANCE = {
    "High": "Suggested response time: within 24 hours.",
    "Medium": "Suggested response time: within the current week.",
    "Low": "Can be handled through normal correspondence.",
    "No_Concern": "No follow-up required.",
}

URGENCY_COLOUR = {
    "High": "#B23A3A",
    "Medium": "#B8860B",
    "Low": "#3A6EA5",
    "No_Concern": "#5A7D5A",
}

EXAMPLES = {
    "Select an example or write your own": "",
    "Financial pressure": "I have not been able to pay my tuition fees this semester and I am worried I will be removed from the rolls.",
    "Routine request": "Could you share the slides from today's Machine Learning lecture?",
    "Emotional distress": "I have been feeling extremely overwhelmed and hopeless lately and I do not know who to talk to.",
    "Safety concern": "A senior student has been repeatedly harassing me online and I do not feel safe on campus anymore.",
    "Falling behind": "I have missed the last three weeks of Statistics due to a family emergency and I am at risk of failing.",
    "Records request": "Could you tell me the process for requesting a bonafide certificate?",
}


st.set_page_config(
    page_title="Student Early-Warning Engine",
    layout="centered",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.6rem; max-width: 820px; }

      .hero-title {
        font-size: 2.0rem; font-weight: 700; color: #1F3864;
        margin-bottom: 0.15rem; letter-spacing: -0.4px;
      }
      .hero-sub { font-size: 0.98rem; color: #5A5A5A; margin-bottom: 0.1rem; }
      .hero-meta { font-size: 0.82rem; color: #8A8A8A; margin-bottom: 1.4rem; }

      .advisory {
        background: #FFF8E6; border-left: 4px solid #B8860B;
        padding: 0.8rem 1rem; border-radius: 3px;
        font-size: 0.88rem; color: #6B5200; margin-bottom: 1.6rem;
      }

      .result-card {
        border: 1px solid #E0E0E0; border-radius: 6px;
        padding: 1.1rem 1.3rem; background: #FFFFFF; margin-bottom: 0.9rem;
      }
      .card-label {
        font-size: 0.73rem; text-transform: uppercase; letter-spacing: 1.1px;
        color: #8A8A8A; margin-bottom: 0.35rem;
      }
      .card-value { font-size: 1.32rem; font-weight: 700; line-height: 1.25; }
      .card-conf { font-size: 0.8rem; color: #777; margin-top: 0.45rem; }

      .bar-track {
        height: 6px; background: #ECECEC; border-radius: 3px;
        margin-top: 0.5rem; overflow: hidden;
      }
      .bar-fill { height: 6px; border-radius: 3px; }

      .action-box {
        background: #F4F7FC; border: 1px solid #D4DEEC;
        border-left: 4px solid #2E5395; border-radius: 4px;
        padding: 1rem 1.2rem; margin-top: 0.4rem;
      }
      .action-label {
        font-size: 0.73rem; text-transform: uppercase; letter-spacing: 1.1px;
        color: #2E5395; font-weight: 600; margin-bottom: 0.3rem;
      }
      .action-value {
        font-size: 1.05rem; font-weight: 600; color: #1F3864; margin-bottom: 0.6rem;
      }
      .action-text { font-size: 0.92rem; color: #333; line-height: 1.6; }

      .timing {
        font-size: 0.88rem; color: #444; margin-top: 0.7rem;
        padding-top: 0.7rem; border-top: 1px solid #E3E9F2;
      }

      .caution {
        background: #FDF0F0; border-left: 4px solid #B23A3A;
        padding: 0.85rem 1.1rem; border-radius: 3px;
        font-size: 0.88rem; color: #7D2525; margin-top: 0.9rem;
      }

      .foot {
        font-size: 0.78rem; color: #9A9A9A; margin-top: 2.2rem;
        padding-top: 1rem; border-top: 1px solid #ECECEC; line-height: 1.6;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def load_embedder():
    return SentenceTransformer(EMBED_MODEL)


@st.cache_resource(show_spinner=False)
def load_classifiers():
    category_model = joblib.load(MODELS_DIR / CATEGORY_FILE)
    urgency_model = joblib.load(MODELS_DIR / URGENCY_FILE)
    return category_model, urgency_model


def analyse(text):
    embedder = load_embedder()
    category_model, urgency_model = load_classifiers()

    vector = embedder.encode([text], convert_to_numpy=True)

    category = category_model.predict(vector)[0]
    category_conf = float(category_model.predict_proba(vector)[0].max())

    urgency = urgency_model.predict(vector)[0]
    urgency_conf = float(urgency_model.predict_proba(vector)[0].max())

    return {
        "category": category,
        "category_confidence": round(category_conf, 2),
        "urgency": urgency,
        "urgency_confidence": round(urgency_conf, 2),
        "recommended_action": RECOMMENDED_ACTION.get(category, "Route for manual review"),
    }


def confidence_words(score):
    if score >= 0.85:
        return "High confidence"
    if score >= 0.65:
        return "Moderate confidence"
    if score >= 0.5:
        return "Low confidence"
    return "Very low confidence"


def render_card(label, value, score, colour):
    pct = int(score * 100)
    st.markdown(
        f"""
        <div class="result-card">
          <div class="card-label">{label}</div>
          <div class="card-value" style="color:{colour};">{value}</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct}%; background:{colour};"></div>
          </div>
          <div class="card-conf">{confidence_words(score)} &middot; {score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown('<div class="hero-title">Student Early-Warning Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Triage support for academic advisors and student services staff</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-meta">Group 6 &middot; SNLP Course Project 2026</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="advisory"><strong>Advisory tool.</strong> This system does not make decisions about students. '
    'It categorises messages so that staff can prioritise which to read first. Every result requires human review.</div>',
    unsafe_allow_html=True,
)

choice = st.selectbox("Example messages", list(EXAMPLES.keys()), label_visibility="collapsed")

message = st.text_area(
    "Student message",
    value=EXAMPLES[choice],
    height=150,
    placeholder="Paste or type a student message here...",
)

analyse_clicked = st.button("Analyse message", type="primary", use_container_width=True)

if analyse_clicked:
    if not message.strip():
        st.warning("Please enter a message before analysing.")
    else:
        with st.spinner("Analysing message..."):
            result = analyse(message)

        st.markdown("")

        left, right = st.columns(2)

        with left:
            render_card(
                "Concern type",
                result["category"].replace("_", " "),
                result["category_confidence"],
                "#1F3864",
            )

        with right:
            render_card(
                "Urgency",
                result["urgency"].replace("_", " "),
                result["urgency_confidence"],
                URGENCY_COLOUR.get(result["urgency"], "#1F3864"),
            )

        guidance = CATEGORY_GUIDANCE.get(result["category"], "Route this message for manual review.")
        timing = URGENCY_GUIDANCE.get(result["urgency"], "")

        st.markdown(
            f"""
            <div class="action-box">
              <div class="action-label">Recommended next step</div>
              <div class="action-value">{result["recommended_action"]}</div>
              <div class="action-text">{guidance}</div>
              <div class="timing">{timing}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        lowest = min(result["category_confidence"], result["urgency_confidence"])
        if lowest < 0.5:
            st.markdown(
                '<div class="caution"><strong>Read this one manually.</strong> '
                'The model is not confident about this message, which usually means the wording is '
                'ambiguous or unlike anything in its training data. Treat the result above as a weak signal only.</div>',
                unsafe_allow_html=True,
            )

        with st.expander("Structured output (what another system receives)"):
            st.json(result)

st.markdown(
    f'<div class="foot">'
    f'Classification is performed locally using {MODEL_LABEL} with a logistic-regression classifier. '
    f'No message is sent to any external service and nothing is stored. '
    f'The hosted demo uses the lighter embedding model to stay within deployment memory limits; '
    f'the repository\'s primary model is MPNet-based.'
    f'</div>',
    unsafe_allow_html=True,
)