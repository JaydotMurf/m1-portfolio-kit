# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run
streamlit run app.py

# Tests (once written)
pytest tests/
pytest tests/test_loader.py   # single file
```

## Architecture

Three-layer pipeline: CSV → loader → charts → Streamlit UI.

- **`core/loader.py`** — sole owner of M1 CSV format knowledge. All raw column names (`Symbol`, `Avg. Price`, etc.) are mapped here via `M1_COLUMN_MAP` and never referenced elsewhere. `load_m1_csv()` returns a normalized DataFrame; `portfolio_summary()` computes scalar metrics from it.
- **`charts/chart_engine.py`** — five Plotly chart functions, each taking a normalized DataFrame and returning a `go.Figure`. All share `BASE_LAYOUT` and `_apply_base()` for consistent dark-mode styling. Design constants (`BG`, `GREEN`, `RED`, `ACCENT`, etc.) live at the top of this file.
- **`app.py`** — Streamlit entry point. Handles file upload, calls `load_m1_csv`, renders `portfolio_summary` metrics, then renders all five charts in tabs. Inline CSS targets Streamlit's internal test-IDs for dark-mode theming.

## Internal column schema

All chart and summary code uses these names exclusively:

`symbol` · `name` · `quantity` · `avg_price` · `cost_basis` · `unrealized_gain_dollar` · `unrealized_gain_pct` · `current_value` · `portfolio_weight_pct`

`portfolio_weight_pct` is derived (not in raw CSV) — computed in `load_m1_csv`.

## Rules

- Phase 1 only (single CSV snapshot). Do not build Phase 2+ features.
- No new packages without updating `requirements.txt` and flagging the addition.
- No hardcoded tickers or personal holdings data.
- Write complete runnable code — no placeholders.
- After completing any implementation step, update the "Current next step" line below.

## Read before starting a session

- `docs/implementation-plan.md` — current phase and next step
- `docs/design-guidelines.md` — color palette, font, component specs
- `docs/app-flow-pages-roles.md` — page states and user flow

## Git rule

After completing a step and confirming tests pass, stage all changed files,
write a conventional commit message (feat:, fix:, docs:, test:, chore:),
and push to main. Do not commit if any test is failing.

## Current next step

Step 1.7 — Final README pass + make repo public (screenshot/GIF, one-command setup block, M1 export instructions, contribution guide link)
