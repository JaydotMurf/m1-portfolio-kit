# M1 Portfolio Kit

[![CI](https://github.com/JaydotMurf/m1-portfolio-kit/actions/workflows/smoke.yml/badge.svg)](https://github.com/JaydotMurf/m1-portfolio-kit/actions/workflows/smoke.yml)
[![PyPI](https://img.shields.io/pypi/v/m1-portfolio-kit)](https://pypi.org/project/m1-portfolio-kit/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Better charts for your M1 Finance portfolio. Drop in your holdings CSV and get
interactive visualizations that M1's built-in interface doesn't offer.

Runs entirely on your local machine — your financial data never leaves your computer.

![Dashboard](docs/web-app-preview.png)

---

## Features

### Portfolio Heatmap (Landing View)

A treemap heatmap greets you on upload — positions grouped by sector, sized by current value,
colored by unrealized return. Click any tile to open a detail panel showing value, cost basis,
return, and snapshot-over-snapshot trends for that position.

### Charts

| Tab | What it answers |
| --- | --- |
| 🥧 Allocation | What percentage of my portfolio is each position? |
| 💵 Gain / Loss ($) | Which positions are making or losing me the most dollars? |
| 📊 Gain / Loss (%) | Which positions have the best/worst return rate, regardless of size? |
| ⚖️ Cost vs Value | What did I pay vs what is it worth now? |
| 🎯 Return vs Weight | Are my biggest positions also my best performers? |
| 🕸️ Radar | How does my portfolio score across performance, diversification, and efficiency? |
| 📊 Concentration | How concentrated is my portfolio? HHI score, top-N weight, weight distribution. |

### Multi-Snapshot Time-Series Tracking

Upload multiple CSVs (one per export date) to track your portfolio over time:

- **📅 Timeline** — Line chart of total portfolio value across snapshots; optional SPY/QQQ overlay
- **📈 Position Trend** — Track individual position value and weight across time
- **🔄 Snapshot Diff** — Compare oldest vs newest: held positions with deltas, new entries, closed positions

### Benchmark Comparison (opt-in)

Enable SPY and/or QQQ overlays on the Timeline tab. Both portfolio and benchmarks are normalized
to % return from the first snapshot date for a fair comparison. Requires internet — the checkbox
is clearly labeled and off by default.

### Concentration Analysis

The Concentration tab gives you three lenses on portfolio concentration — all computed from your
CSV with no external data:

- **HHI Score** — Herfindahl-Hirschman Index (0–10,000). Labeled: Diversified / Moderate / Concentrated.
- **Top-N Weight** — Cumulative % held in your top N positions. Slider adjustable.
- **Weight Distribution** — Histogram of position weights across your portfolio.

### Privacy Guarantee

No data is written to disk. Uploaded CSVs live in memory for the browser session only.
Phase 1 and Phase 2 make zero network requests. The benchmark overlay is strictly opt-in
and clearly labeled.

---

## Setup

### pip (quickest)

```bash
pip install m1-portfolio-kit
m1kit
```

The app opens at `http://localhost:8501`.
To enable the optional SPY/QQQ benchmark overlay: `pip install "m1-portfolio-kit[benchmarks]"`

### Docker (no Python required)

```bash
docker build -t m1-portfolio-kit .
docker run -p 8501:8501 m1-portfolio-kit
```

The app opens at `http://localhost:8501`.
To enable the optional SPY/QQQ benchmark overlay, add `RUN pip install yfinance` after the
`pip install -r requirements.txt` line in the Dockerfile before building.

### From source

Requires Python 3.10+

```bash
git clone https://github.com/JaydotMurf/m1-portfolio-kit.git
cd m1-portfolio-kit
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Getting your M1 CSV

1. Log in to [M1 Finance](https://m1.com)
2. Go to **Invest → Portfolio → Holdings**
3. Click the **...** overflow menu (top right of the holdings list)
4. Select **Export CSV**
5. Save the file — no renaming needed
6. Upload it in the app

The export includes all positions with cost basis, current value, and unrealized gain/loss.
M1 does not include closed positions in this export.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, test, and PR instructions.

---

## Roadmap

- [x] **Phase 1** — Single snapshot analysis (heatmap, 7 charts, summary metrics, radar)
- [x] **Phase 2** — Multi-snapshot time-series tracking (timeline, position trends, snapshot diffs)
- [x] **Phase 3** — Benchmark overlay, sector classification, heatmap landing, click-to-detail
- [x] **Phase 4** — Concentration metrics (HHI, top-N weight, weight histogram)
- [x] **Phase 5** — Packaging and distribution (Docker, PyPI, `m1kit` CLI)

---

## License

MIT
