
import streamlit as st
import pandas as pd
import unicodedata
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="MethodMatch — PM Style Classifier", layout="centered")

# --- Global font + stronger enforcement on form labels ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"], * {
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif !important;
    }
    .question-label {
        font-weight: 600;
        font-size: 1.05rem;
        margin-top: 0.9rem;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True
)

STYLE_INFO = {
    "Lean: Design Build": "Single contract for design+construction enabling early builder input, fast-track overlap, and unified accountability.",
    "Lean: CMAR": "CM engaged early for precon, then builder under GMP; early input, open-book costs, strong phasing/constructability.",
    "Lean: JOC": "Programmatic unit-price contracting via task orders; great for many small/repetitive jobs and fast admin.",
    "Agile: IPD": "Multiparty agreement with shared risk/reward; early trades, TVD, pull planning, and high transparency for complex work.",
    "Agile: P3": "Private partner may design/build/finance/operate; shifts lifecycle risk with performance-tied payments.",
    "Predictive: DBB": "Complete design then low-bid construction; roles clear, best when scope stable and compliance strict.",
    "Predictive: BOT": "Concessionaire finances, designs, builds, operates, then transfers back; aligns lifecycle incentives."
}

def normalize_label(s: str) -> str:
    if pd.isna(s):
        return s
    # NFKD decomposes math italic/compat characters to plain ASCII where possible
    s = unicodedata.normalize("NFKD", str(s))
    # Replace fancy dashes with hyphen
    for d in ["—","–","−","‒"]:
        s = s.replace(d, "-")
    # Replace non‑breaking/thin spaces with normal spaces and collapse
    for sp in ["\u00A0","\u2009","\u200A","\u200B"]:
        s = s.replace(sp, " ")
    s = " ".join(s.split())
    return s

st.title("MethodMatch — PM Style Classifier")
st.markdown("Upload a **weights CSV** or rely on defaults in the repo. Columns required: `question`, `question_text`, `answer_text` (optional: `answer_code`, `answer_label`) plus one column per style.")

DEFAULT_PATHS = ["pm_style_weights_CALIBRATED.csv", "pm_style_weights_FULL.csv"]
df_default, chosen_path = None, None
for p in DEFAULT_PATHS:
    if Path(p).exists():
        df_default, chosen_path = pd.read_csv(p), p
        break

uploaded = st.file_uploader("Weights CSV", type=["csv"])
if uploaded is not None:
    df = pd.read_csv(uploaded)
    st.success("Weights loaded from upload ✅")
elif df_default is not None:
    df = df_default
    st.info(f"Using default weights found in repo: **{chosen_path}**")
else:
    st.error("No weights available. Upload a CSV or include one in the repo root.")
    st.stop()

# Validate columns
base_cols = {"question", "question_text", "answer_text"}
style_cols = [c for c in df.columns if c in STYLE_INFO.keys()]
if not base_cols.issubset(set(df.columns)) or not style_cols:
    st.error("CSV is missing required columns. Expected base columns and at least one style column.")
    st.write("Found columns:", list(df.columns))
    st.stop()

has_code  = "answer_code"  in df.columns
has_label = "answer_label" in df.columns

# Sidebar preview
with st.sidebar:
    st.subheader("Weights Preview")
    st.dataframe(df.head(12), use_container_width=True)

# ---- Single-response UI (no batch scoring) ----
st.header("Answer the 12 questions")
answers = {}
for q in sorted(df["question"].unique()):
    sub = df[df["question"] == q].copy()
    qtext = normalize_label(sub["question_text"].iloc[0])

    # Display label pref: clean `answer_label` if present else clean `answer_text`
    if has_label:
        sub["display"] = sub["answer_label"].apply(normalize_label)
    else:
        sub["display"] = sub["answer_text"].apply(normalize_label)

    # Scoring key pref: code if present else raw text (not normalized)
    sub["key"] = sub["answer_code"] if has_code else sub["answer_text"]

    opts = list(sub["display"].unique())
    default_idx = opts.index("Unknown") if "Unknown" in opts else 0

    st.markdown(f'<span class="question-label">Q{q} — {qtext}</span>', unsafe_allow_html=True)
    choice = st.radio("", options=opts, index=default_idx, key=f"Q{q}")
    answers[q] = sub.loc[sub["display"] == choice, "key"].iloc[0]

if st.button("Compute Style"):
    scores = {s: 0.0 for s in STYLE_INFO.keys()}
    for q, key in answers.items():
        if has_code:
            row = df[(df["question"]==q) & (df["answer_code"]==key)]
        else:
            row = df[(df["question"]==q) & (df["answer_text"]==key)]
        if not row.empty:
            for s in STYLE_INFO.keys():
                scores[s] += float(row.iloc[0][s])

    top = max(scores, key=scores.get)
    st.subheader("Scores")
    st.dataframe(pd.DataFrame([scores]))
    st.success(f"**Recommended style: {top}**")
    st.info(STYLE_INFO[top])

    # downloadable single-result CSV
    out = {"timestamp": datetime.now().isoformat()}
    for q in sorted(answers.keys()):
        out[f"Q{q}"] = answers[q]
    for s in STYLE_INFO.keys():
        out[s] = scores[s]
    out["recommended_style"] = top
    out_df = pd.DataFrame([out])
    st.download_button(
        label="Download this result (CSV)",
        data=out_df.to_csv(index=False).encode("utf-8"),
        file_name="methodmatch_single_result.csv",
        mime="text/csv",
    )
