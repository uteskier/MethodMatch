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

st.set_page_config(page_title="MethodMatch — PM Style Classifier", layout="centered")
st.title("MethodMatch — PM Style Classifier")

st.markdown("Upload a **weights CSV** (or use the in-repo default).")

# Try default weights in repo
DEFAULT_PATHS = ["pm_style_weights_CALIBRATED.csv", "pm_style_weights_FULL.csv"]
default_df = None
for p in DEFAULT_PATHS:
    if Path(p).exists():
        default_df = pd.read_csv(p)
        break

file = st.file_uploader("Weights CSV", type=["csv"], help="Columns: question, question_text, answer_text, and one column per style")
if file is not None:
    df = pd.read_csv(file)
    st.success("Weights loaded from upload ✅")
elif default_df is not None:
    df = default_df
    st.info(f"Using default weights found in repo: **{p}**")
else:
    st.warning("No weights available. Please upload a CSV.")
    st.stop()

required = {"question","question_text","answer_text"} | set(STYLE_INFO.keys())
if not required.issubset(set(df.columns)):
    st.error("CSV is missing required columns. Expected: 'question', 'question_text', 'answer_text' and one column per style.")
    st.stop()

st.header("Answer the 12 questions")
answers = {}
for q in sorted(df["question"].unique()):
    sub = df[df["question"]==q]
    qtext = sub["question_text"].iloc[0]
    opts = list(sub["answer_text"].unique())
    answers[q] = st.radio(f"Q{q} — {qtext}", options=opts, index=opts.index("Unknown") if "Unknown" in opts else 0)

if st.button("Compute Style"):
    scores = {s: 0.0 for s in STYLE_INFO.keys()}
    for q, ans in answers.items():
        row = df[(df["question"]==q) & (df["answer_text"]==ans)]
        if not row.empty:
            for s in STYLE_INFO.keys():
                scores[s] += float(row.iloc[0][s])

    top = max(scores, key=scores.get)
    st.subheader("Scores")
    st.dataframe(pd.DataFrame([scores]))
    st.success(f"**Recommended style: {top}**")
    st.info(STYLE_INFO[top])