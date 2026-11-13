# SolarShield-AI app (Streamlit)

Research explorer for SILSO monthly sunspot numbers, cycle summaries, baseline backtests, and model freeze status.

## Run

From the **repository root** (the folder that contains `app/`, `data/`, and `reports/`):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-app.txt
streamlit run app/Home.py
pytest tests/test_app_lib.py
```

The app only reads files already in the repository. It does not retrain models or issue operational risk alerts.

## Layout

- `app/Home.py` — latest SSN and model status
- `app/pages/` — Forecasts, Cycles, Trends, Data downloads, Model status
- `data/processed/` — cleaned monthly series and cycle summary
- `reports/` — backtests, development runs, model freeze registry
