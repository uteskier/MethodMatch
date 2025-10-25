import pandas as pd

STYLES = ['Lean: Design Build', 'Lean: CMAR', 'Lean: JOC', 'Agile: IPD', 'Agile: P3', 'Predictive: DBB', 'Predictive: BOT']

def load_weights(path):
    w = pd.read_csv(path)
    weights_map = {}
    for _, row in w.iterrows():
        q = int(row["question"])
        a = row["answer_text"]
        weights_map[(q, a)] = {s: float(row[s]) for s in STYLES}
    return weights_map

def score_row(weights_map, answers):
    scores = {s: 0.0 for s in STYLES}
    for q, a in answers.items():
        if (q, a) in weights_map:
            for s in STYLES:
                scores[s] += weights_map[(q, a)][s]
    top = max(scores, key=scores.get)
    return scores, top

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Batch score responses Q1..Q12")
    ap.add_argument("--weights", required=True)
    ap.add_argument("--responses", required=True)
    ap.add_argument("--out", default="scored_responses.csv")
    args = ap.parse_args()

    weights_map = load_weights(args.weights)
    resp = pd.read_csv(args.responses)
    outs = []
    for i, row in resp.iterrows():
        answers = {q: row[f"Q{q}"] for q in range(1,13)}
        scores, top = score_row(weights_map, answers)
        outs.append({"row": i, **answers, **scores, "recommended_style": top})
    pd.DataFrame(outs).to_csv(args.out, index=False)
    print(f"Wrote {args.out}")