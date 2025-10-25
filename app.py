import streamlit as st
import pandas as pd
from pathlib import Path

STYLE_INFO = {
    "Lean: Design Build": "Single contract for design+construction enabling early builder input, fast-track overlap, and unified accountability.",
    "Lean: CMAR": "CM engaged early for precon, then builder under GMP; early input, open-book costs, strong phasing/constructability.",
    "Lean: JOC": "Programmatic unit-price contracting via task orders; great for many small/repetitive jobs and fast admin.",
    "Agile: IPD": "Multiparty agreement w/ shared risk/reward; early trades, TVD, pull planning, high transparency for complex work.",
    "Agile: P3": "Private partner may design/build/finance/operate; shifts lifecycle risk with performance-tied payments.",
    "Predictive: DBB": "Complete design then low-bid construction; roles clear, best when scope stable and compliance strict.",
    "Predictive: BOT": "Concessionaire finances, designs, builds, operates, then transfers back; aligns lifecycle incentives."
}

# --- Global font (optional) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif;
    }
    .question-label {
        font-weight: 600;
        font-size: 1.05rem;
        margin-top: 0.75rem;
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="MethodMatch — PM Style Classifier", layout="centered")
st.title("MethodMatch — PM Style Classifier")

st.markdown("Upload a **weights CSV** (or use the in-repo default).")

DEFAULT_PATHS = ["pm_style_weights_CALIBRATED.csv", "pm_style_weights_FULL.csv"]
default_df = None
chosen_path = None
for p in DEFAULT_PATHS:
    if Path(p).exists():
        default_df = pd.read_csv(p)
        chosen_path = p
        break

file = st.file_uploader("Weights CSV", type=["csv"], help="Columns: question, question_text, answer_text (and optionally answer_code, answer_label), plus one style column per style")
if file is not None:
    df = pd.read_csv(file)
    st.success("Weights loaded from upload ✅")
elif default_df is not None:
    df = default_df
    st.info(f"Using default weights found in repo: **{chosen_path}**")
else:
    st.warning("No weights available. Please upload a CSV.")
    st.stop()

# Determine columns
required_base = {"question","question_text","answer_text"}
style_cols = [c for c in df.columns if c in STYLE_INFO.keys()]
if not required_base.issubset(set(df.columns)) or not style_cols:
    st.error("CSV is missing required columns. Expected: 'question', 'question_text', 'answer_text' and one column per style.")
    st.stop()

has_code = "answer_code" in df.columns
has_label = "answer_label" in df.columns

# Build per-question options mapping
st.header("Answer the 12 questions")
answers = {}
for q in sorted(df["question"].unique()):
    sub = df[df["question"]==q].copy()
    qtext = sub["question_text"].iloc[0]

    # For display, prefer answer_label if present, else answer_text.
    if has_label:
        sub["display"] = sub["answer_label"]
    else:
        sub["display"] = sub["answer_text"]

    # For scoring key, prefer answer_code (stable), else answer_text.
    if has_code:
        sub["key"] = sub["answer_code"]
    else:
        sub["key"] = sub["answer_text"]

    opts = list(sub["display"].unique())

    # Default to "Unknown" if present
    default_index = opts.index("Unknown") if "Unknown" in opts else 0

    # Render nicely
    st.markdown(f'<span class="question-label">Q{q} — {qtext}</span>', unsafe_allow_html=True)
    choice = st.radio("", options=opts, index=default_index, key=f"Q{q}")
    chosen_key = sub.loc[sub["display"]==choice, "key"].iloc[0]
    answers[q] = chosen_key

if st.button("Compute Style"):
    scores = {s: 0.0 for s in STYLE_INFO.keys()}

    for q, chosen_key in answers.items():
        # Match row by (question, key column). If we don't have answer_code, key==answer_text.
        if has_code:
            row = df[(df["question"]==q) & (df.get("answer_code")==chosen_key)]
        else:
            row = df[(df["question"]==q) & (df["answer_text"]==chosen_key)]
        if not row.empty:
            for s in STYLE_INFO.keys():
                scores[s] += float(row.iloc[0][s])

    top = max(scores, key=scores.get)
    st.subheader("Scores")
    st.dataframe(pd.DataFrame([scores]))
    st.success(f"**Recommended style: {top}**")
    st.info(STYLE_INFO[top])
