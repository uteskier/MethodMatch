import pandas as pd, numpy as np, unicodedata, re

def norm(s):
    if pd.isna(s): return s
    s = unicodedata.normalize("NFKD", str(s)).replace("—","-").replace("–","-").replace("−","-")
    return re.sub(r"\s+", " ", s).strip()

def canon_level(s):
    t = norm(s).lower()
    if t.startswith("co-"): return "Co-Located"
    return {"very high":"Very High","high":"High","medium":"Medium","low":"Low","extreme":"Extreme"}.get(t, norm(s).capitalize())

def canon_q2(s):
    u = norm(s).upper()
    if "FINANCE + OPERATE" in u: return "Finance + Operate"
    if "SHORT" in u: return "Short-term O&M"
    if "LONG" in u: return "Long-term O&M"
    if "NONE" in u: return "None"
    return norm(s)

def canon_q3(s):
    u = norm(s).upper()
    if "SMALL" in u: return "Small (1 Approver)"
    if "MEDIUM" in u: return "Medium (2-3 Approvers)"
    if "LARGE" in u: return "Large (4-6 Approvers)"
    if "MEGA" in u: return "Mega (7+ Approvers)"
    return norm(s)

def canon_q4(s):
    u = norm(s).upper()
    if "LUMP" in u: return "Lump Sum"
    if u == "GMP": return "GMP"
    if "COST" in u: return "Cost-Plus"
    if "PERFORMANCE" in u: return "Performance-Based"
    return norm(s)

def canon_q7(s):
    t = norm(s).replace("(JOC)","").strip()
    u = t.upper()
    if "COMPETITIVE" in u: return "Competitive Bid"
    if "NEGOTIATED" in u: return "Negotiated"
    if "FRAMEWORK" in u: return "Framework"
    if "BEST" in u: return "Best-Value"
    return "-".join(w.capitalize() for w in t.split("-"))

# Read files (must exist in repo root)
W = pd.read_csv("pm_style_weights_CALIBRATED.csv")  # your existing layout (preserves row order)
C = pd.read_csv("pm_style_case_studies.csv")

meta = {"question","question_text","answer_text","answer_code","answer_label"}
STYLES = [c for c in W.columns if c not in meta]

# Canonicalize cases just in case
C["expected_style"] = C["expected_style"].map(lambda s: "Lean: Design Build" if norm(s)=="Lean: Design-Build" else norm(s))
C["Q1"]  = C["Q1"].map(lambda s: norm(s).replace("–","-"))
C["Q2"]  = C["Q2"].map(canon_q2)
C["Q3"]  = C["Q3"].map(canon_q3)
C["Q4"]  = C["Q4"].map(canon_q4)
C["Q5"]  = C["Q5"].map(canon_level)
C["Q6"]  = C["Q6"].map(lambda s: "Fast-track" if "fast" in norm(s).lower() else norm(s).capitalize())
C["Q7"]  = C["Q7"].map(canon_q7)
C["Q8"]  = C["Q8"].map(lambda s: norm(s).replace("–","-"))
C["Q9"]  = C["Q9"].map(canon_level)
C["Q10"] = C["Q10"].map(canon_level)
C["Q11"] = C["Q11"].map(canon_level)
C["Q12"] = C["Q12"].map(canon_level)

# Build one-hot using the exact answer order in W
q_opts = {q: list(W.loc[W["question"]==q, "answer_text"].values) for q in sorted(W["question"].unique())}
def enc(row):
    feats=[]
    for q in range(1,13):
        opts=q_opts[q]; v=row[f"Q{q}"]
        feats.extend([1.0 if v==opt else 0.0 for opt in opts])
    return np.array(feats,float)

X = np.vstack([enc(r) for _,r in C.iterrows()])
Y = np.column_stack([(C["expected_style"]==s).astype(float).values for s in STYLES])

# Ridge: Wcoef = (X^T X + αI)^(-1) X^T Y
alpha = 1.0
XtX = X.T @ X
XtY = X.T @ Y
Wcoef = np.linalg.solve(XtX + alpha*np.eye(XtX.shape[0]), XtY)  # (features x styles)

# Scatter back into W, preserving row order & headers
W_new = W.copy()
k = 0
for q in sorted(q_opts.keys()):
    opts = q_opts[q]
    for i, opt in enumerate(opts):
        mask = (W_new["question"]==q) & (W_new["answer_text"]==opt)
        for si, st in enumerate(STYLES):
            W_new.loc[mask, st] = float(Wcoef[k+i, si])
    k += len(opts)

W_new.to_csv("pm_style_weights_CALIBRATED.csv", index=False)
print("✅ Rewrote pm_style_weights_CALIBRATED.csv")
