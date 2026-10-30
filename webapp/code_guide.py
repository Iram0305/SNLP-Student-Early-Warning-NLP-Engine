"""
Plain-English guide to the project's source files, shown in the "Code"
tab of the web app.

Each part is anchored to a piece of text in the file (not a line number),
so the explanations still line up if the code is edited later. A part runs
from its anchor line to the line before the next part's anchor.
"""

CODE_FILES = [
    # ---------------------------------------------------------------- data
    {
        "path": "src/preprocessing/generate_dataset.py",
        "group": "1. Data",
        "title": "Synthetic dataset generator",
        "summary": "Creates the labelled training data. No real student data exists for this task, so we wrote message templates for every (category, urgency) pair and fill in slots such as the course name to get variety.",
        "parts": [
            ("import argparse", "Imports and seed", "random.seed(42) fixes the random generator so the same dataset is produced every time. This makes the project reproducible."),
            ("TEMPLATES = {", "Template bank", "A dictionary keyed by (category, urgency). Each value is a list of realistic student sentences. {course} is a slot that gets replaced with a real course name. This is where the six categories and four urgency levels are defined in practice."),
            ("COURSES = [", "Slot values", "Course names used to fill the {course} slot, so the model does not memorise one subject."),
            ("RECOMMENDED_ACTION = {", "Action lookup", "Maps each category to the office that should handle it. The model never predicts the action; it is looked up from the predicted category."),
            ("def fill_slots", "fill_slots()", "Replaces every {course} placeholder in a template with a randomly chosen course."),
            ("def generate", "generate()", "Loops over every template group, samples n_per_class messages, gives each one an id like MSG0001 and writes the rows to a CSV."),
            ("if __name__", "Command-line entry", "Lets you run the file directly with --n_per_class and --out arguments."),
        ],
    },
    {
        "path": "src/preprocessing/preprocess.py",
        "group": "1. Data",
        "title": "Cleaning and train/val/test split",
        "summary": "Cleans the raw text and splits it into training (70%), validation (15%) and test (15%) sets, stratified so every category appears in each split in the same proportion.",
        "parts": [
            ("def clean_text", "clean_text()", "Deliberately light cleaning: trims the ends and collapses repeated whitespace. Case and punctuation are kept because sentence-embedding models use them."),
            ("def main", "main()", "Loads the raw CSV, cleans it, drops duplicate or empty rows, then calls train_test_split twice: first 70/30, then the 30 is halved into validation and test. stratify= keeps the category balance and random_state=42 makes the split repeatable."),
            ("if __name__", "Command-line entry", "Runs the split with paths given on the command line."),
        ],
    },
    {
        "path": "src/preprocessing/add_review_examples.py",
        "group": "1. Data",
        "title": "Adding review-style No_Concern examples (Week 7)",
        "summary": "Group 5's real course reviews were over-flagged as Academic difficulty because the model had never seen ordinary reviews. This script adds 40 review-style No_Concern examples (28 train / 6 val / 6 test).",
        "parts": [
            ("review_comments = [", "The new examples", "Forty ordinary course-review sentences, praising or neutrally describing a course. They teach the model that talking about a course is not the same as struggling with it."),
            ("n_train = 28", "Split sizes", "How many of the 40 examples go to each split, roughly 70/15/15 like the original data."),
            ("for split, comments in parts.items():", "Appending to the CSVs", "For each split, reads the existing CSV, builds new rows labelled No_Concern / No_Concern, and writes the file back. Re-running embed_v2.py and improved_model_v2.py afterwards retrains the model."),
        ],
    },
    # -------------------------------------------------------------- models
    {
        "path": "src/models/baseline.py",
        "group": "2. Models",
        "title": "Week 2 baseline: TF-IDF + Logistic Regression",
        "summary": "The simplest reasonable model, used as the reference point. TF-IDF turns each message into a sparse vector of word and word-pair weights, and Logistic Regression learns which words signal each label.",
        "parts": [
            ("def build_pipeline", "build_pipeline()", "A scikit-learn Pipeline: TfidfVectorizer (unigrams and bigrams, English stop words removed, sublinear term frequency) followed by LogisticRegression with class_weight='balanced' so rare classes are not ignored."),
            ("def train_and_evaluate", "train_and_evaluate()", "Fits the pipeline on train.csv, predicts test.csv, prints a classification report, saves the report and confusion matrix to results/ and the model to saved/."),
            ("if __name__", "Entry point", "Trains two separate models: one for category, one for urgency."),
        ],
    },
    {
        "path": "src/models/embed.py",
        "group": "2. Models",
        "title": "Week 3 embeddings: all-MiniLM-L6-v2",
        "summary": "Converts every message into a 384-number sentence embedding. Unlike TF-IDF, embeddings capture meaning, so 'I can't pay my fees' and 'money is tight' end up close together.",
        "parts": [
            ("MODEL_NAME =", "Model choice", "all-MiniLM-L6-v2 is a small, fast sentence-transformer. It is also what the hosted Streamlit app uses because of the 1 GB memory limit."),
            ("def embed_split", "embed_split()", "Reads one split, encodes all texts in one call, and saves the vectors (.npy) plus the labels so training does not have to re-encode every time."),
            ("def main", "main()", "Loads the model once and embeds train, val and test."),
        ],
    },
    {
        "path": "src/models/improved_model.py",
        "group": "2. Models",
        "title": "Week 3 classifier on MiniLM embeddings",
        "summary": "Trains Logistic Regression on the cached MiniLM embeddings. Same evaluation as the baseline so the two can be compared directly.",
        "parts": [
            ("def load_split", "load_split()", "Loads the saved embedding matrix and matching label CSV for one split."),
            ("def train_and_evaluate", "train_and_evaluate()", "Fits LogisticRegression (balanced class weights) on train embeddings, evaluates on test, saves results and improved_<target>.joblib."),
        ],
    },
    {
        "path": "src/models/embed_v2.py",
        "group": "2. Models",
        "title": "Week 4 embeddings: all-mpnet-base-v2",
        "summary": "Same idea as embed.py but with MPNet, a larger model that produces 768-number embeddings and generally understands sentences better. This is the primary model of the project.",
        "parts": [
            ("MODEL_NAME =", "Model choice", "all-mpnet-base-v2: slower and bigger than MiniLM, but the strongest general-purpose sentence-transformer at the time we chose it."),
            ("def embed_split", "embed_split()", "Encodes one split and caches the vectors in src/models/embeddings_v2/ (not tracked in git)."),
            ("def main", "main()", "Embeds all three splits."),
        ],
    },
    {
        "path": "src/models/improved_model_v2.py",
        "group": "2. Models",
        "title": "Week 4 classifier with validation-based model selection",
        "summary": "Tries two classifiers on the MPNet embeddings and keeps whichever scores the best macro F1 on the validation set. The test set is only touched once, at the end.",
        "parts": [
            ("def load_split", "load_split()", "Loads cached MPNet embeddings and labels."),
            ("def pick_best_classifier", "pick_best_classifier()", "Fits Logistic Regression and a linear SVM, scores both on validation with macro F1 (every class counts equally), and returns the winner. probability=True on the SVM lets us still output a confidence."),
            ("def train_and_evaluate", "train_and_evaluate()", "Selects the classifier, evaluates on the test set, saves week4_<target>_test_report.csv, the confusion matrix and week4_<target>.joblib."),
        ],
    },
    {
        "path": "src/models/pipeline_v2.py",
        "group": "3. Reusable asset",
        "title": "The reusable NLP asset: analyze_message()",
        "summary": "The single function other groups (and this web app) call. Text goes in; category, urgency, two confidences and a recommended action come out as a dictionary.",
        "parts": [
            ("RECOMMENDED_ACTION = {", "Action lookup", "Category to recommended office. Kept as a lookup so a human-readable rule, not the model, decides where a case is routed."),
            ("_embedder = None", "Lazy globals", "Models start as None and are loaded on first use, then reused. Loading MPNet takes seconds, encoding one message takes milliseconds."),
            ("def _load_models", "_load_models()", "Loads the MPNet encoder and the two saved Week 4 classifiers once."),
            ("def analyze_message", "analyze_message()", "1) encode the text into a 768-d vector, 2) predict category and urgency, 3) take the highest class probability as the confidence, 4) look up the action. Returns the JSON contract documented in the README."),
            ("if __name__", "Self-test", "Runs three example messages when the file is executed directly."),
        ],
    },
    {
        "path": "src/api/app.py",
        "group": "3. Reusable asset",
        "title": "FastAPI service",
        "summary": "Wraps analyze_message() in a REST API so any program (in any language) can call it over HTTP.",
        "parts": [
            ("class SingleMessage", "Request schemas", "Pydantic models describe and validate the JSON body each endpoint accepts."),
            ("@app.get(\"/\")", "Health check", "GET / returns a small status message so callers can check the service is up."),
            ("@app.post(\"/analyze-message\")", "POST /analyze-message", "Analyses one message."),
            ("@app.post(\"/analyze-feedback\")", "POST /analyze-feedback", "Analyses a batch and returns only confident concerns (support signals)."),
            ("@app.post(\"/feedback-summary\")", "POST /feedback-summary", "Analyses a batch and returns counts by category and urgency plus the high-priority items."),
        ],
    },
    {
        "path": "src/api/integration.py",
        "group": "4. Integration",
        "title": "Batch helpers for Group 5 feedback",
        "summary": "Functions to analyse many feedback comments at once, pick out support signals, summarise them, and read/write JSON or CSV files.",
        "parts": [
            ("def analyze_feedback_batch", "analyze_feedback_batch()", "Accepts plain strings or {id, text} items, skips empty ones, and runs analyze_message on each."),
            ("def find_support_signals", "find_support_signals()", "Keeps only results that are a concern and whose category confidence is at least the threshold (0.5 by default)."),
            ("def summarise_signals", "summarise_signals()", "Counts results per category and urgency and lists the High-urgency items."),
            ("def load_feedback_file", "load_feedback_file()", "Reads a JSON file ({items:[...]}) or a CSV with a text/feedback/comment column."),
            ("def save_triage_results", "save_triage_results()", "Writes results back out as JSON or CSV."),
            ("def process_group5_file", "process_group5_file()", "One-call convenience: load, analyse, save, print a short report."),
        ],
    },
    {
        "path": "demo/run_group5.py",
        "group": "4. Integration",
        "title": "Group 5 file handoff",
        "summary": "Reads Group 5's 38 feedback comments and writes the triage reply file we send back to them.",
        "parts": [
            ("INPUT_FILE =", "File locations", "Input and output live in data/integration/. File names contain spaces on purpose; keep them as they are."),
            ("NOT_SUPPORT =", "Support-signal rule", "No_Concern and Administrative are not welfare concerns, so they never count as support signals."),
            ("def main", "main()", "Analyses every comment, applies the rule (concern AND confidence >= 0.5), builds the agreed reply format with advisory_only: true, and saves it."),
        ],
    },
    # ---------------------------------------------------------- evaluation
    {
        "path": "src/evaluation/compare_all_models.py",
        "group": "5. Evaluation",
        "title": "Baseline vs Week 3 vs Week 4 comparison",
        "summary": "Reads the three saved test reports and puts the per-class F1 scores side by side, with the improvement of Week 4 over each earlier model.",
        "parts": [
            ("def compare", "compare()", "Loads the three report CSVs, keeps the f1-score column from each, adds difference columns and saves comparison_all_<target>.csv."),
        ],
    },
    {
        "path": "src/evaluation/error_analysis.py",
        "group": "5. Evaluation",
        "title": "Error analysis and confidence check",
        "summary": "Lists every wrong test prediction and checks whether the model is less confident when it is wrong, which is what justifies sending low-confidence results to a human.",
        "parts": [
            ("def load_test_split", "load_test_split()", "Loads the cached MPNet test embeddings and labels."),
            ("def analyze", "analyze()", "Predicts the test set, records predicted label, confidence and correct/incorrect for every row, and saves all predictions and the errors to results/."),
            ("def robustness_check", "robustness_check()", "Compares mean confidence on correct vs wrong predictions. A clear gap means confidence is a useful signal for human review."),
        ],
    },
    # ------------------------------------------------------------- web app
    {
        "path": "webapp/server.py",
        "group": "6. This web app",
        "title": "Local web server",
        "summary": "The FastAPI server behind this page. It loads the Week 4 model in the background, exposes JSON endpoints for the UI, serves the HTML, and can shut itself down.",
        "parts": [
            ("ROOT = Path", "Paths", "Finds the repo root so imports and data files work no matter where the server is started from."),
            ("CATEGORY_GUIDANCE = {", "Guidance text", "Short advice shown under each prediction. Written by us, not generated by the model."),
            ("_state = {", "Background model loading", "The model takes a few seconds to load, so it loads in a thread while the page is already usable. The UI polls /api/status."),
            ("@app.post(\"/api/analyze\")", "POST /api/analyze", "Runs analyze_message and adds guidance, timing and a needs_review flag when either confidence is below 0.5."),
            ("@app.post(\"/api/batch\")", "POST /api/batch", "Batch triage for the dashboard: same support-signal rule as run_group5.py, plus counts for the charts."),
            ("@app.get(\"/api/code\")", "Code viewer endpoints", "Lists the files in this guide and returns a file's source with its explanations."),
            ("@app.post(\"/api/shutdown\")", "POST /api/shutdown", "Used by the Shut down button and stop_app.bat. Replies first, then ends the Python process."),
        ],
    },
]


def build_annotations(source, parts):
    """Turn (anchor, title, text) parts into line ranges for the viewer."""
    lines = source.splitlines()
    found = []
    for anchor, title, text in parts:
        line_no = next((i for i, line in enumerate(lines, start=1) if anchor in line), None)
        if line_no is not None:
            found.append({"start": line_no, "title": title, "text": text})

    found.sort(key=lambda a: a["start"])
    for i, ann in enumerate(found):
        end = found[i + 1]["start"] - 1 if i + 1 < len(found) else len(lines)
        while end > ann["start"] and not lines[end - 1].strip():
            end -= 1
        ann["end"] = end
    return found
