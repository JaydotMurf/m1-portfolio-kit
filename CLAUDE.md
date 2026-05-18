# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (runtime)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Setup (development — includes pytest)
pip install -r requirements.txt -r requirements-dev.txt

# Run
streamlit run app.py

# Tests
pytest tests/
pytest tests/test_loader.py   # single file
```

## Architecture

Three-layer pipeline: CSV → loader → charts → Streamlit UI.

- **`core/loader.py`** — sole owner of M1 CSV format knowledge. Raw M1 column names
  (`Symbol`, `Avg. Price`, etc.) are mapped to internal names via `M1_COLUMN_MAP` and
  must never appear anywhere else in the codebase. Key functions:
  - `load_m1_csv(source)` — validates schema, normalizes types, derives `portfolio_weight_pct`
  - `portfolio_summary(df)` — returns a flat dict of scalar metrics for the metric row
  - `parse_snapshot_date(filename)` — extracts ISO or Month-DD-YYYY dates from filenames
  - `load_snapshots(files, date_map)` — builds a `dict[date_str → DataFrame]`, sorted ascending
  - `snapshot_diff(snapshots)` — outer-merges oldest vs newest snapshot; tags rows `held / new / closed`

- **`charts/chart_engine.py`** — eight Plotly chart functions, each accepting a normalized
  DataFrame or snapshots dict and returning a `go.Figure`. All share `BASE_LAYOUT` and
  `_apply_base()`. Design constants are defined at the top of this file and must be used
  exclusively — never reference raw hex values in chart code. Functions:
  - `plot_allocation(df)` — donut chart by portfolio weight
  - `plot_gainloss_dollar(df)` — horizontal bar, unrealized gain/loss ($)
  - `plot_gainloss_pct(df)` — horizontal bar, unrealized return (%)
  - `plot_cost_vs_value(df)` — grouped vertical bar, cost basis vs current value
  - `plot_return_vs_weight(df)` — scatter/bubble, return % vs portfolio weight
  - `plot_portfolio_radar(df)` — five-dimension radar (performance, win rate, diversification,
    capital efficiency, gain breadth); all scores computed from CSV only, no external data
  - `plot_portfolio_timeline(snapshots)` — Phase 2 line chart of total value over time
  - `plot_position_delta(snapshots, symbol)` — Phase 2 dual-axis trend for one ticker

- **`app.py`** — Streamlit entry point. Branches on `len(uploaded_files)`:
  - **Single file (Phase 1):** `load_m1_csv` → metrics → position cards → raw table →
    6-tab chart view (allocation, gain/loss $, gain/loss %, cost vs value, return vs
    weight, radar)
  - **Multiple files (Phase 2):** date pickers → `load_snapshots` → metrics + raw table
    on latest snapshot → 8-tab view (timeline, position trend, snapshot diff, + the 5
    single-snapshot charts applied to the latest DataFrame)
  - CSS injection via `st.markdown(unsafe_allow_html=True)` enforces dark theme over
    Streamlit's internal component test-IDs. `.streamlit/config.toml` locks the base
    theme. Both layers are required — do not remove either.

- **`tests/test_loader.py`** — 20 pytest tests covering all loader functions and all
  chart functions via synthetic CSV fixtures. No real holdings data anywhere in tests.

## Internal column schema

All chart and summary code uses these names exclusively:

`symbol` · `name` · `quantity` · `avg_price` · `cost_basis` · `unrealized_gain_dollar` · `unrealized_gain_pct` · `current_value` · `portfolio_weight_pct`

`portfolio_weight_pct` is derived (not in raw CSV) — computed in `load_m1_csv`.

## Design system constants

All color, font, and layout values are defined at the top of `charts/chart_engine.py`.
Always use these constants — never inline hex strings in chart or UI code:

| Constant   | Value       | Meaning                                      |
|------------|-------------|----------------------------------------------|
| `BG`       | `#0d1117`   | Page and chart background                    |
| `PAPER`    | `#0d1117`   | Plotly paper background                      |
| `GRID`     | `#21262d`   | Chart gridlines, borders, dividers           |
| `TEXT`     | `#e6edf3`   | Primary text, chart labels                   |
| `MUTED`    | `#8b949e`   | Secondary labels, axis titles, zero-lines    |
| `GREEN`    | `#3fb950`   | Positive gain only — never decorative        |
| `RED`      | `#f85149`   | Negative loss only — never decorative        |
| `ACCENT`   | `#58a6ff`   | Current value, links, selected tab, info     |
| `FONT`     | `"monospace"` | All chart and UI text                      |
| `PALETTE`  | `px.colors.qualitative.T10` | Multi-series charts (donut, etc.) |

Green and red are signal colors. They encode financial meaning. Do not use them for
decoration, status indicators, or anything other than gain/loss.

## Rules

**Code quality:**
- Write complete, runnable code — no placeholders or stubs.
- No hardcoded tickers or personal holdings data anywhere in the codebase.
- `loader.py` is the seam. Raw M1 column names live only in `M1_COLUMN_MAP` — nowhere else.
- Use design constants from `chart_engine.py`, not inline hex values.
- No new packages without updating the appropriate requirements file and flagging the addition.

**Dependencies:**
- Runtime dependencies → `requirements.txt`
- Development/test dependencies → `requirements-dev.txt`
- Phase 3 optional dependencies (e.g., `yfinance`) → `requirements-optional.txt` (create if
  it does not exist). Optional deps must never be imported unconditionally — guard with
  `try/except ImportError` and surface a clear `st.warning()` if not installed.

**External data and privacy:**
- Phase 1 and Phase 2 make zero network requests. The app must be fully offline-capable.
- Phase 3 benchmark fetches are opt-in only: the user must explicitly enable a UI control
  before any network call is made. The control must be clearly labeled as requiring internet.
- CSV files are never written to disk. `data/` and all `*.csv` files are gitignored.

**Testing:**
- Every new function in `loader.py` requires at least one test in `tests/test_loader.py`.
- Every new chart function requires a test asserting it returns a `go.Figure`.
- All tests must pass before committing. Do not commit if `pytest tests/` fails.
- Use synthetic CSV data in tests — never real holdings data.

**Theming:**
- Dark mode is a product decision, not a default. Do not add a light mode toggle.
- The theme is enforced by two layers that must both remain: `.streamlit/config.toml`
  (base theme) and CSS injection in `app.py` (component-level overrides). Do not remove
  or bypass either layer.

## Skills

Load and follow `~/.claude/skills/starting-project-session/SKILL.md` at the start of every session.

## Read before starting a session

- `work-in-progress.md` — master development reference: current state, what's built, what's next
- `docs/implementation-plan.md` — phase roadmap and step-level detail
- `docs/design-guidelines.md` — full color palette, typography, component specs
- `docs/app-flow-pages-roles.md` — page states and user flow

## Git rule

After completing a step and confirming tests pass, stage all changed files, write a
conventional commit message (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), and push to
main. Do not commit if any test is failing.

## Current next step

Phase 2 complete (steps 2.1–2.4). Now beginning Phase 3.

**Phase 3, Step 3.1 — Benchmark overlay on the portfolio timeline chart:**
- Create `requirements-optional.txt` with `yfinance>=0.2`
- Add `fetch_benchmark(tickers, start, end)` to `core/loader.py`
- Add opt-in checkbox to the Timeline tab (multi-snapshot mode only), labeled to indicate
  a network call
- Extend `plot_portfolio_timeline()` to accept and render optional benchmark traces
- Convert both portfolio and benchmark to % return from first snapshot date for comparison
- Add mocked benchmark tests to `tests/test_loader.py`
