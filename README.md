# 📈 M1 Portfolio Kit

Better charts for your M1 Finance portfolio. Drop in your holdings CSV,
get interactive visualizations that M1's built-in interface doesn't offer.

Built with Python, pandas, and Plotly. Runs entirely on your local machine —
your financial data never leaves your computer.

## Charts

| Chart | What It Shows |
|---|---|
| Allocation | Portfolio weight by current value (donut) |
| Gain / Loss ($) | Unrealized dollar gain or loss per position |
| Gain / Loss (%) | Unrealized return % per position, normalized for size |
| Cost vs Value | What you paid vs what it's worth today |
| Return vs Weight | Are your biggest positions also your best performers? |

## Setup

Requires Python 3.10+

    git clone https://github.com/JaydotMurf/m1-portfolio-kit.git
    cd m1-portfolio-kit
    python -m venv venv
    source venv/bin/activate   # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    streamlit run app.py

## Getting Your M1 CSV

1. Log in to M1 Finance
2. Navigate to Invest → Portfolio → Holdings
3. Click the ... overflow menu
4. Select Export CSV
5. Upload the file in the app

## Project Structure

    m1-portfolio-kit/
    ├── app.py               # Streamlit entry point
    ├── requirements.txt
    ├── core/
    │   └── loader.py        # M1 CSV ingestion and normalization
    ├── charts/
    │   └── chart_engine.py  # Plotly chart functions
    └── data/                # Drop CSVs here (gitignored)

## Roadmap

- [x] Phase 1 — Single snapshot analysis
- [ ] Phase 2 — Multi-snapshot time-series tracking
- [ ] Phase 3 — Benchmark comparison (SPY, QQQ)
- [ ] Phase 4 — Concentration and risk metrics

## License

MIT
