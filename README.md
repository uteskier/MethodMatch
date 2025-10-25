# MethodMatch — PM Style Classifier (Streamlit)

This app recommends one of 7 project delivery/management styles based on answers to 12 questions.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

Upload `pm_style_weights_CALIBRATED.csv` or start with `pm_style_weights_FULL.csv` (zeros).

## Calibrate weights from case studies
Edit `pm_style_case_studies.csv` then:
```bash
python calibrate_weights.py
```
This writes `pm_style_weights_CALIBRATED.csv` used by the app.

## Batch scoring
If you have a CSV of answers (columns `Q1..Q12`):
```bash
python score_responses.py --weights pm_style_weights_CALIBRATED.csv --responses responses.csv --out scored_responses.csv
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a **public GitHub repo**.
2. Go to https://share.streamlit.io, click **New app**, select your repo, branch, and `app.py` as the entry point.
3. Click **Deploy**.
4. The app will use `pm_style_weights_CALIBRATED.csv` if present, otherwise `pm_style_weights_FULL.csv`.
5. You can still upload a new weights CSV at runtime via the file uploader.