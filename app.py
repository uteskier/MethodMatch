import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# ----------------------------
# Config & Style
# ----------------------------
st.set_page_config(page_title="MethodMatch — PM Style Classifier", layout="centered")

# Global font + nicer question label styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif;
    }
    .question-label {
        font-weight: 600;
        font-size: 1.05rem;
        margin-top: 0.9rem;
        display: block;
    }
    .muted { color: #6b7280; }
    </style>
    """,
    unsafe_allow_html=True
)

# Style dictionary (used for column validation + display descriptions)
STYLE_INFO = {
    "Lean: Design Build": "Single contract for design+construction enabling early builder input, fast-track overlap, and unified accountability.",
    "Lean: CMAR": "CM engaged early for precon, then builder under GMP; early input, open-book costs, strong phasing/constructability.",
    "Lean: JOC": "Programmatic unit-price contracting via task orders; great for many small/repetitive jobs and fast admin.",
    "Agile: IPD": "Multiparty agreement with shared risk/reward; early trades, target value delivery, pull planning, and high transparency for complex work.",
    "Agile: P3": "Private partner may design/build/finance/operate; shifts lifecycle risk with performance-tied payments.",
    "Predictive: DBB": "Complete design then low-bid construction; roles clear, best when scope stable and compliance strict.",
    "Predictive: BOT": "Concessionaire finances, designs, builds, operates, then transfers back; aligns lifecycle incentives."
}

# ----------------------------
# Load weights CSV
# ----------------------------
st.title("MethodMatch — PM Style Classifier")

st.markdown("Upload a **weights CSV** or rely on defaults in the repo. The CSV must include columns: `question`, `question_text`, `answer_text` (and optionally `answer_code`, `answer_label`), plus one column for each style.")

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

# Validate required columns
base_cols = {"question", "question_text", "answer_text"}
style_cols = [c for c in df.columns if c in STYLE_INFO.keys()]
if not base_cols.issubset(set(df.columns)) or not style_cols:
    st.error("CSV is missing required columns. Expected base columns and at least one style column.")
    st.write("Found columns:", list(df.columns))
    st.stop()

has_code = "answer_code" in df.columns
has_label = "answer_label" in df.columns

# Sidebar: show a quick preview & download a blank template if needed
with st.sidebar:
    st.subheader("Weights Preview")
    st.caption("First 10 rows from the loaded weights file:")
    st.dataframe(df.head(10), use_container_width=True)
    # Help text
    st.markdown("""
    **Columns**
    - `question`: integer (1..12)
    - `question_text`: displayed under the radio
    - `answer_text`: scoring key or raw text
    - `answer_code` *(optional)*: stable key for scoring
    - `answer_label` *(optional)*: pretty display text
    - One column per style: numeric weights (can be negative)
    """)

# ----------------------------
# Single-response UI
# ----------------------------
st.header("Answer the 12 questions")    
answers = {}
for q in sorted(df["question"].unique()):
    sub = df[df["question"] == q].copy()
    qtext = sub["question_text"].iloc[0]

    # Display label preference
    sub["display"] = sub["answer_label"] if has_label else sub["answer_text"]
    # Scoring key preference
    sub["key"] = sub["answer_code"] if has_code else sub["answer_text"]

    opts = list(sub["display"].unique())
    default_idx = opts.index("Unknown") if "Unknown" in opts else 0

    st.markdown(f'<span class="question-label">Q{q} — {qtext}</span>', unsafe_allow_html=True)
    choice = st.radio("", options=opts, index=default_idx, key=f"Q{q}")
    answers[q] = sub.loc[sub["display"] == choice, "key"].iloc[0]

# Compute button
if st.button("Compute Style"):
    # Initialize scores
    scores = {s: 0.0 for s in STYLE_INFO.keys()}

    # Sum weights for chosen answers
    for q, key in answers.items():
        if has_code:
            row = df[(df["question"]==q) & (df["answer_code"]==key)]
        else:
            row = df[(df["question"]==q) & (df["answer_text"]==key)]
        if not row.empty:
            for s in STYLE_INFO.keys():
                scores[s] += float(row.iloc[0][s])

    # Top style
    top = max(scores, key=scores.get)

    st.subheader("Scores")
    st.dataframe(pd.DataFrame([scores]))
    st.success(f"**Recommended style: {top}**")
    st.info(STYLE_INFO[top])

    # Offer a downloadable CSV for this single response
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

# ----------------------------
# Batch Scoring (optional)
# ----------------------------
st.header("Batch scoring (optional)")
st.caption("Upload a CSV with columns Q1..Q12 to score many responses at once.")
resp_csv = st.file_uploader("Responses CSV (Q1..Q12)", type=["csv"], key="resp")
if resp_csv is not None:
    resp = pd.read_csv(resp_csv)
    # Validate columns
    needed_cols = [f"Q{i}" for i in range(1, 13)]
    if not set(needed_cols).issubset(set(resp.columns)):
        st.error("Responses CSV must contain columns Q1..Q12.")
    else:
        # Prepare a weights lookup
        if has_code:
            key_field = "answer_code"
        else:
            key_field = "answer_text"
        # Build map
        wmap = {}
        for _, r in df.iterrows():
            k = (int(r["question"]), str(r[key_field]))
            wmap[k] = {s: float(r[s]) for s in STYLE_INFO.keys()}

        results = []
        for i, row in resp.iterrows():
            scores = {s: 0.0 for s in STYLE_INFO.keys()}
            for q in range(1, 13):
                key = row[f"Q{q}"]
                k = (q, str(key))
                if k in wmap:
                    for s in STYLE_INFO.keys():
                        scores[s] += wmap[k][s]
            top = max(scores, key=scores.get)
            results.append({"row": i, **{f"Q{q}": row.get(f"Q{q}", "") for q in range(1,13)}, **scores, "recommended_style": top})

        res_df = pd.DataFrame(results)
        st.dataframe(res_df.head(25))
        st.download_button(
            label="Download all results (CSV)",
            data=res_df.to_csv(index=False).encode("utf-8"),
            file_name="methodmatch_scored_responses.csv",
            mime="text/csv",
        )

