import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge

STYLES = ['Lean: Design Build', 'Lean: CMAR', 'Lean: JOC', 'Agile: IPD', 'Agile: P3', 'Predictive: DBB', 'Predictive: BOT']

def main():
    weights = pd.read_csv("pm_style_weights_FULL.csv")
    cs = pd.read_csv("pm_style_case_studies.csv")

    q_cats = {}
    for q in sorted(weights["question"].unique()):
        q_cats[q] = list(weights.loc[weights["question"]==q, "answer_text"].unique())

    def encode_row(row):
        feats = []
        for q in range(1,13):
            opts = q_cats[q]
            val = row[f"Q{q}"]
            feats.extend([1.0 if val == o else 0.0 for o in opts])
        return np.array(feats, dtype=float)

    X = np.vstack([encode_row(r) for _, r in cs.iterrows()])
    Y = np.zeros((len(cs), len(STYLES)))
    for i, st in enumerate(STYLES):
        Y[:, i] = (cs["expected_style"] == st).astype(float).values

    alpha = 1.0
    coefs = []
    for i in range(len(STYLES)):
        m = Ridge(alpha=alpha, fit_intercept=False)
        m.fit(X, Y[:, i])
        coefs.append(m.coef_)
    coefs = np.array(coefs)

    out = weights.copy()
    idx = 0
    for q in range(1,13):
        opts = q_cats[q]
        for o in opts:
            mask = (out["question"]==q) & (out["answer_text"]==o)
            for si, st in enumerate(STYLES):
                out.loc[mask, st] = coefs[si, idx]
            idx += 1

    out.to_csv("pm_style_weights_CALIBRATED.csv", index=False)
    print("Wrote pm_style_weights_CALIBRATED.csv")

if __name__ == "__main__":
    main()