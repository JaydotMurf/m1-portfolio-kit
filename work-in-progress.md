# M1 Portfolio Kit — Work In Progress

> Master development reference document. Tracks current state, planned work, and future
> direction. Serves as the source of truth for feature scope, architecture, and roadmap.
> Will form the foundation of the final README prior to go-live.

---

## Table of Contents

1. [Application Summary](#application-summary)
2. [Features and Functionality](#features-and-functionality)
3. [Architecture](#architecture)
4. [Work Completed](#work-completed)
5. [Work In Progress](#work-in-progress)
6. [Future Improvements](#future-improvements)

---

## Application Summary

**M1 Portfolio Kit** is a privacy-first, open-source portfolio visualization tool built
specifically for M1 Finance investors. Where M1's native interface gives you a balance
and a percentage, M1 Portfolio Kit gives you a command center — the kind of terminal-grade
analytical depth that institutional traders take for granted, rebuilt for individual
investors who want to understand what their money is actually doing.

The premise is brutally simple: drop in the CSV you already export from M1's Holdings
screen, and within seconds you have six interactive charts, a position-by-position
performance breakdown, a radar chart scoring your portfolio across five dimensions, and
the ability to track your entire portfolio's evolution across time by uploading multiple
dated snapshots. No login. No server. No subscription. Your financial data never leaves
your machine.

The aesthetic is deliberate. Dark background, monospace font, high-contrast signal colors —
a developer's Bloomberg terminal scaled down for the retail investor. Every design
decision exists to serve legibility of financial data, not to decorate a marketing page.
Color means something: green signals a gain, red signals a loss, blue marks the current
value. No exceptions.

Built on Python, pandas, Streamlit, and Plotly, the tool is intentionally approachable
for contributors, transparent in its architecture, and additive in its roadmap — each
phase ships independently, and no half-built feature bleeds into completed work.

---

## Features and Functionality

### CSV Ingestion and Normalization

The application accepts M1 Finance's native holdings CSV export with zero preprocessing
required from the user. The `core/loader.py` module is the sole owner of M1's raw column
format. It validates the schema on ingest, raises clear errors if columns are missing,
strips comma-formatted currency strings, casts all numeric columns to float, removes
M1's appended totals rows, and derives a `portfolio_weight_pct` column before returning
a clean, typed DataFrame. Nothing outside `loader.py` ever sees a raw M1 column name.

### Portfolio Summary Metrics

A six-card metric row renders at the top of every dashboard view, giving an instant
snapshot of portfolio health:

- **Total Value** — sum of all current position values
- **Total Gain / Loss** — aggregate unrealized dollar gain with return percentage delta
- **Positions** — count of active holdings in the uploaded snapshot
- **Winners** — count of positions with a positive unrealized gain
- **Losers** — count of positions with a negative unrealized gain
- **Best Performer** — ticker symbol of the highest unrealized return percentage

### Position Cards

A compact visual grid renders all held positions sorted by current value descending,
five per row. Each card displays the ticker symbol, current dollar value, portfolio
weight percentage, return percentage, and dollar gain/loss. Gain and loss values are
color-coded using the design system's green/red signal tokens, giving immediate
directional context at a glance without opening a chart.

### Holdings Data Table

A collapsible expander below the metric row surfaces the full normalized DataFrame with
professional formatting. Column headers are rendered in title case. Currency columns
display with `$` and comma formatting. Unrealized gain/loss columns show directional
arrows (▲/▼) alongside the value and are background-colored green or red, making the
table scannable as a performance heatmap.

### Chart Tab: Portfolio Allocation (Donut)

A donut chart breaking down the portfolio by current value weight per position. Slices
are colored using Plotly's T10 qualitative palette applied in value-descending order.
The center annotation displays the total portfolio value. Hover tooltips surface position
dollar value and weight percentage. The chart answers: *What percentage of my portfolio
is each position?*

### Chart Tab: Unrealized Gain / Loss — Dollar ($)

A horizontal bar chart sorted ascending by dollar gain/loss per position. Bars are
green for gains and red for losses, with a dotted zero-line reference. Hover tooltips
show position name, dollar gain/loss, and return percentage. The chart answers: *Which
positions are making or losing me the most money in dollar terms?*

### Chart Tab: Unrealized Gain / Loss — Percent (%)

A horizontal bar chart sorted ascending by return percentage per position. Same green/red
color encoding and zero-line reference as the dollar chart, with swapped primary and
secondary metrics in the tooltip. The chart answers: *Which positions have the best or
worst return rate, regardless of size?*

### Chart Tab: Cost Basis vs Current Value

A grouped vertical bar chart with one bar pair per position, sorted by current value
descending. The cost basis bar is rendered in muted gray at 80% opacity; the current
value bar is rendered in accent blue. A horizontal legend above the chart identifies
each series. The chart answers: *What did I pay for each position versus what it is
worth today?*

### Chart Tab: Return vs Portfolio Weight (Bubble)

A scatter/bubble chart plotting every position at the intersection of its portfolio
weight (x-axis) and unrealized return (y-axis). Bubble size is proportional to current
value, scaled from 10px to 70px. A dotted zero-line divides gainers from losers. The
chart answers: *Are my largest positions also my best performers — or am I heavily
concentrated in underperformers?*

### Chart Tab: Portfolio Snapshot Radar

A five-dimensional radar chart scoring the portfolio across analytically derived
dimensions, all computed from the CSV without any external data:

- **Performance** — weighted-average unrealized return by portfolio weight, clamped and
  normalized to a 0–100 score
- **Win Rate** — percentage of positions with a positive unrealized gain
- **Diversification** — inverse Herfindahl-Hirschman Index normalized so perfect
  equal-weight scores 100
- **Capital Efficiency** — ratio of total current value to total cost basis, scaled
  from a 0.5× floor to a 2.0× ceiling
- **Gain Breadth** — gains as a share of total absolute P&L, measuring whether the
  portfolio's gains are broad or concentrated in a few positions

Each spoke shows a score from 0 to 100 with a hover tooltip that shows the underlying
metric value driving the score.

### Multi-Snapshot: Portfolio Timeline

When multiple CSVs are uploaded, a date-keyed snapshot registry is built and the
Timeline tab renders a line chart of total portfolio value across all snapshot dates.
Markers appear at each snapshot point with hover showing the exact date and dollar value.
This gives a visible record of how the portfolio has grown or contracted between exports.

### Multi-Snapshot: Position Trend

A dropdown in the Position Trend tab allows selecting any ticker that appears in any
snapshot. The chart renders two series on a dual axis: current value in dollars (left
axis, accent blue, solid line) and portfolio weight percentage (right axis, muted gray,
dashed line). Tracking both together reveals whether a position's value growth is
outpacing or lagging the rest of the portfolio.

### Multi-Snapshot: Snapshot Diff

The Snapshot Diff tab compares the oldest and most recent snapshot side by side,
categorizing every position into one of three states:

- **Held** — present in both snapshots, with value change, return change (in percentage
  points), and weight change displayed
- **New** — opened after the oldest snapshot, showing entry value and current return
- **Closed** — present in the oldest snapshot but not the newest, showing final known
  value and return

### Date Parsing from Filenames

When multiple CSVs are uploaded, the application attempts to parse a date from each
filename automatically, supporting both ISO format (`YYYY-MM-DD`) and M1's
Month-DD-YYYY format (`Jan-15-2024`). If parsing succeeds, the date picker pre-populates
with the extracted value; the user can override any date before analysis proceeds.
Duplicate dates across files are detected and rejected with a clear error.

### Error Handling

All CSV loading paths surface errors in Streamlit's native `st.error()` component:
schema validation failures list the missing columns and the columns actually found;
unexpected exceptions display the raw exception message. In both cases `st.stop()`
halts rendering so the uploader remains visible for re-upload without a page refresh.

### Dark-Only Theme

A locked dark theme is enforced through two layers: a `.streamlit/config.toml` that
sets the base theme to dark and pins all design tokens, and CSS injected via
`st.markdown(..., unsafe_allow_html=True)` that overrides Streamlit's internal component
test-IDs for metric cards, tab selection, and the page background. There is no light
mode toggle; the dark terminal aesthetic is a product decision, not a default setting.

### Privacy Guarantee

No data is written to disk. Streamlit's `st.file_uploader` holds uploaded files in
memory for the duration of the browser session and discards them on refresh. The
`.gitignore` explicitly excludes the `data/` directory and all `*.csv` files. Phase 1
makes zero network requests. Phase 3's optional benchmark fetch will require an explicit
opt-in UI control.

---

## Architecture

### Directory Structure

```
m1-portfolio-kit/
├── app.py                        # Streamlit entry point — UI, routing, rendering
├── core/
│   ├── __init__.py
│   └── loader.py                 # CSV ingestion, normalization, snapshot registry, diffs
├── charts/
│   ├── __init__.py
│   └── chart_engine.py           # Eight Plotly chart functions + design constants
├── tests/
│   ├── __init__.py
│   └── test_loader.py            # 20 pytest tests covering loader + all chart functions
├── docs/
│   ├── implementation-plan.md    # Phase roadmap and step-by-step development plan
│   ├── design-guidelines.md      # Design token spec and component rulebook
│   ├── app-flow-pages-roles.md   # Page states, user flow, state machine
│   ├── masterplan.md             # High-level blueprint and strategic overview
│   └── screenshot-0[1-8].png     # Dashboard screenshots for README
├── .streamlit/
│   └── config.toml               # Streamlit theme: dark, monospace, design tokens
├── .claude/
│   └── settings.local.json       # Claude Code permissions (local dev only)
├── requirements.txt              # Runtime dependencies: streamlit, pandas, numpy, plotly
├── requirements-dev.txt          # Dev dependencies: pytest
├── CLAUDE.md                     # AI assistant instructions for this repo
├── CONTRIBUTING.md               # Setup, test, and PR guide for contributors
├── README.md                     # Public-facing project documentation
├── work-in-progress.md           # This file
└── data/                         # .gitkeep — CSV uploads never committed here
```

---

### High-Level Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         USER'S BROWSER                                  ║
║                      http://localhost:8501                              ║
╚══════════════════════════════╦═══════════════════════════════════════════╝
                               ║  HTTP (localhost only)
╔══════════════════════════════▼═══════════════════════════════════════════╗
║                        FRONTEND LAYER                                   ║
║                      Streamlit Runtime                                  ║
║  ┌─────────────────┐  ┌───────────────────┐  ┌───────────────────────┐ ║
║  │  File Uploader  │  │  Metric Cards     │  │  Tab Navigator        │ ║
║  │  st.file_       │  │  st.columns(6)    │  │  st.tabs()            │ ║
║  │  uploader()     │  │  st.metric()      │  │  st.plotly_chart()    │ ║
║  └────────┬────────┘  └───────────────────┘  └───────────────────────┘ ║
║  ┌────────┴───────────────────────────────────────────────────────────┐ ║
║  │  CSS Injection Layer (dark theme, metric cards, tab accent color)  │ ║
║  └────────────────────────────────────────────────────────────────────┘ ║
╚══════════════════════════════╦═══════════════════════════════════════════╝
                               ║  File-like objects (in-memory only)
╔══════════════════════════════▼═══════════════════════════════════════════╗
║                       MIDDLEWARE / DATA LAYER                           ║
║                         core/loader.py                                  ║
║  ┌───────────────────┐  ┌───────────────────┐  ┌─────────────────────┐ ║
║  │  load_m1_csv()    │  │ portfolio_        │  │ load_snapshots()    │ ║
║  │  Schema validate  │  │ summary()         │  │ snapshot_diff()     │ ║
║  │  Type casting     │  │ Scalar metrics    │  │ parse_snapshot_     │ ║
║  │  Normalization    │  │ for metric row    │  │  date()             │ ║
║  └────────┬──────────┘  └───────────────────┘  └─────────────────────┘ ║
╚═══════════╦══════════════════════════════════════════════════════════════╝
            ║  Normalized pandas DataFrame(s)
╔═══════════▼══════════════════════════════════════════════════════════════╗
║                         CHART ENGINE LAYER                              ║
║                      charts/chart_engine.py                             ║
║                                                                         ║
║  Single-Snapshot Charts          Multi-Snapshot Charts                  ║
║  ┌────────────────────┐          ┌────────────────────────────────────┐ ║
║  │ plot_allocation()  │          │ plot_portfolio_timeline()          │ ║
║  │ plot_gainloss_     │          │ plot_position_delta()              │ ║
║  │   dollar()         │          └────────────────────────────────────┘ ║
║  │ plot_gainloss_     │                                                 ║
║  │   pct()            │          Design Constants                       ║
║  │ plot_cost_vs_      │          ┌────────────────────────────────────┐ ║
║  │   value()          │          │ BG, PAPER, GRID, TEXT, MUTED       │ ║
║  │ plot_return_vs_    │          │ GREEN, RED, ACCENT, FONT           │ ║
║  │   weight()         │          │ BASE_LAYOUT, PALETTE               │ ║
║  │ plot_portfolio_    │          └────────────────────────────────────┘ ║
║  │   radar()          │                                                 ║
║  └────────────────────┘                                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

External Connectivity (Phase 3 — opt-in only, not yet built)
╔══════════════════════════════════════════════════════════════════════════╗
║  yfinance API  ──►  SPY / QQQ historical price data                     ║
║  (network call — requires user to explicitly toggle benchmark overlay)  ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

### Lower-Level Process Flow Diagram

```
════════════════════════════════════════════════════════════════
  PHASE 1 — SINGLE CSV FLOW
════════════════════════════════════════════════════════════════

  User uploads 1 CSV
        │
        ▼
  app.py detects len(uploaded_files) == 1
        │
        ▼
  load_m1_csv(file)
    ├── pd.read_csv(source)
    ├── dropna(how="all")              remove M1 totals row
    ├── validate required columns ─── FAIL ─► st.error() + st.stop()
    ├── rename via M1_COLUMN_MAP
    ├── _clean_numeric() on comma-formatted cols
    ├── pd.to_numeric() on plain numeric cols
    ├── dropna(subset=["symbol"])
    └── derive portfolio_weight_pct
        │
        ▼
  portfolio_summary(df)
    ├── total_value, total_cost, total_gain, total_return_pct
    ├── positions, winners, losers
    └── largest_position, best_performer, worst_performer
        │
        ▼
  _render_metrics(summary)          ─► st.columns(6) + st.metric()
        │
        ▼
  _render_position_cards(df)        ─► HTML card grid (5 per row)
        │
        ▼
  _render_raw_table(df)             ─► st.expander + st.dataframe (styled)
        │
        ▼
  st.tabs([6 tabs])
    ├── tab1: plot_allocation(df)      ─► go.Pie (donut)
    ├── tab2: plot_gainloss_dollar(df) ─► go.Bar (horizontal)
    ├── tab3: plot_gainloss_pct(df)    ─► go.Bar (horizontal)
    ├── tab4: plot_cost_vs_value(df)   ─► go.Bar (grouped vertical)
    ├── tab5: plot_return_vs_weight(df)─► go.Scatter (bubble)
    └── tab6: plot_portfolio_radar(df) ─► go.Scatterpolar

════════════════════════════════════════════════════════════════
  PHASE 2 — MULTI-CSV FLOW
════════════════════════════════════════════════════════════════

  User uploads N ≥ 2 CSVs
        │
        ▼
  app.py renders date_input() per file
    ├── parse_snapshot_date(filename) ─── auto-detect ISO / MDY format
    └── user can override any date
        │
        ▼
  load_snapshots(files, date_map)
    ├── detect duplicate dates ─────────── FAIL ─► st.error() + st.stop()
    ├── load_m1_csv() on each file
    └── return dict sorted by date ascending
        │
        ▼
  latest_df = snapshots[last_date]
        │
        ▼
  _render_metrics(portfolio_summary(latest_df))
  _render_raw_table(latest_df)
        │
        ▼
  st.tabs([8 tabs])
    ├── tab_timeline:
    │     plot_portfolio_timeline(snapshots)
    │       ├── extract dates + sum values
    │       └── go.Scatter (lines+markers)
    │
    ├── tab_trend:
    │     st.selectbox(all_symbols)
    │     plot_position_delta(snapshots, symbol)
    │       ├── extract per-symbol value + weight per snapshot
    │       └── go.Scatter dual-axis (value left / weight right)
    │
    ├── tab_diff:
    │     snapshot_diff(snapshots)
    │       ├── outer merge oldest vs newest on "symbol"
    │       ├── compute value_change, return_change_pp, weight_change_pp
    │       └── tag rows: held / new / closed
    │     Render 3 sub-tables: Held, New, Closed
    │
    └── tabs 1–5: same single-snapshot charts on latest_df
```

---

### Third-Party Integration Flow (Phase 3 — Planned)

```
════════════════════════════════════════════════════════════════
  PHASE 3 — BENCHMARK OVERLAY (OPT-IN EXTERNAL DATA)
════════════════════════════════════════════════════════════════

  User views Timeline tab (multi-snapshot mode)
        │
        ▼
  st.checkbox("Show benchmark comparison (SPY / QQQ)")
        │
        ├── OFF (default) ─────────────────────► render timeline as-is
        │                                         (no network call)
        └── ON
              │
              ▼
        st.multiselect(["SPY", "QQQ"])
              │
              ▼
        yfinance.download(tickers, start=dates[0], end=dates[-1])
              │
              ├── SUCCESS ─────────────────────► normalize to % return
              │                                   from first snapshot date
              │                                   add trace per benchmark
              │                                   portfolio also converted
              │                                   to % return for comparison
              │                                   ─► st.plotly_chart()
              │
              └── FAILURE (network error)
                    │
                    ▼
              st.warning("Could not fetch benchmark data.")
              Render timeline without overlay

════════════════════════════════════════════════════════════════
  PHASE 3 — SECTOR MAPPING (USER-SUPPLIED CSV)
════════════════════════════════════════════════════════════════

  User uploads sector_map.csv
  ┌────────────────────────────────────┐
  │  symbol  │  sector                 │
  │  AAPL    │  Technology             │
  │  MSFT    │  Technology             │
  │  JPM     │  Financials             │
  └────────────────────────────────────┘
        │
        ▼
  loader merges sector_map onto holdings DataFrame
        │
        ▼
  plot_sector_allocation(df)          ─► go.Pie (donut, by sector)
  snapshot_diff updated to show sector deltas
  Unmapped symbols flagged with st.warning()

════════════════════════════════════════════════════════════════
  PHASE 4 — PACKAGING AND DISTRIBUTION
════════════════════════════════════════════════════════════════

  Docker Build
  ┌──────────────────────────────────────┐
  │  Dockerfile                          │
  │  COPY . /app                         │
  │  RUN pip install -r requirements.txt │
  │  EXPOSE 8501                         │
  │  CMD streamlit run app.py            │
  └──────────────────────────────────────┘
        │
        ▼
  docker run -p 8501:8501 m1-portfolio-kit
  ─► Zero Python install required on host machine

  PyPI Distribution
  ┌──────────────────────────────────────┐
  │  pyproject.toml                      │
  │  entry_point: m1kit → app.py         │
  │  pip install m1-portfolio-kit        │
  │  m1kit                               │
  └──────────────────────────────────────┘
```

---

## Work Completed

### Phase 1 — Single Snapshot Analysis

#### Project Scaffold (Step 1.1)
- [x] Created directory structure: `core/`, `charts/`, `tests/`, `docs/`, `data/`
- [x] Initialized virtual environment and `requirements.txt`
- [x] `core/__init__.py` and `charts/__init__.py` module stubs
- [x] `.gitignore` excluding `data/`, `*.csv`, `venv/`, `__pycache__/`
- [x] Initial commit and GitHub remote established

#### CSV Ingestion and Normalization (Step 1.2)
- [x] `load_m1_csv()` in `core/loader.py`
- [x] `M1_COLUMN_MAP` mapping M1 raw column names to internal snake_case schema
- [x] `REQUIRED_COLUMNS` validation with descriptive `ValueError` on mismatch
- [x] `_clean_numeric()` strips commas and `$` from currency-formatted columns
- [x] `pd.to_numeric(errors="coerce")` on plain numeric columns
- [x] `dropna(subset=["symbol"])` removes M1's summary rows
- [x] Derived `portfolio_weight_pct` column

#### Portfolio Summary Metrics (Step 1.3)
- [x] `portfolio_summary()` returning a flat dict with 10 scalar metrics
- [x] `total_value`, `total_cost`, `total_gain`, `total_return_pct`
- [x] `positions`, `winners`, `losers`
- [x] `largest_position`, `best_performer`, `worst_performer`

#### Five Core Charts (Step 1.4)
- [x] `plot_allocation()` — donut chart with center annotation and T10 palette
- [x] `plot_gainloss_dollar()` — horizontal bar, green/red, dotted zero-line
- [x] `plot_gainloss_pct()` — horizontal bar, green/red, dotted zero-line
- [x] `plot_cost_vs_value()` — grouped vertical bar, MUTED/ACCENT series
- [x] `plot_return_vs_weight()` — bubble scatter, size scaled to current_value
- [x] `BASE_LAYOUT` and `_apply_base()` shared across all five charts
- [x] All hover tooltips follow design spec: dark surface, monospace, `<extra></extra>`

#### Streamlit App Shell (Step 1.5)
- [x] `st.set_page_config()` — wide layout, `📈` favicon, collapsed sidebar
- [x] CSS injection for dark background, metric cards, tab accent, divider color
- [x] File uploader with privacy help text
- [x] `_render_metrics()` with six `st.metric()` cards in proportional columns
- [x] `_render_raw_table()` inside a collapsed `st.expander()`
- [x] Six-tab layout (`st.tabs()`) rendering all charts via `st.plotly_chart()`
- [x] Error handling: `ValueError` → `st.error()` + `st.stop()`
- [x] Error handling: unexpected exception → `st.error()` + `st.stop()`
- [x] Empty state: `st.info()` + `st.stop()` when no file uploaded

#### Smoke Tests and CI (Step 1.6)
- [x] `tests/test_loader.py` with 20 passing pytest tests
- [x] Synthetic `SAMPLE_CSV` and `SAMPLE_CSV_2` fixtures (no real holdings data)
- [x] Schema shape and column name assertions
- [x] Portfolio weight sum assertion (≈100.0)
- [x] Comma-formatted currency parsing assertion
- [x] Winner/loser count assertion
- [x] Missing column `ValueError` assertion with column name in message
- [x] All five Phase 1 chart functions asserted to return `go.Figure`
- [x] GitHub Actions CI workflow running `pytest tests/` on every push

#### README and Open-Source Release (Step 1.7)
- [x] `README.md` with features table, setup instructions, M1 export guide, roadmap
- [x] Eight dashboard screenshots in `docs/`
- [x] `CONTRIBUTING.md` with ground rules, setup, and PR guide
- [x] Repository made public on GitHub

#### UX Polish (Post-Phase 1 Additions)
- [x] Dark mode locked via `.streamlit/config.toml` — prevents user override
- [x] Metric card overflow fixed (`white-space: nowrap; overflow: visible`)
- [x] Raw data table: title-case column headers replacing snake_case
- [x] Raw data table: directional arrows (▲/▼) in gain/loss columns
- [x] Raw data table: background color coding on gain/loss cells (green/red)
- [x] `pandas.DataFrame.map()` replacing deprecated `applymap()` for pandas 2.1+
- [x] `plot_portfolio_radar()` — five-dimension radar, all metrics computed from CSV
- [x] `_render_position_cards()` — compact ticker grid with color-coded P&L

---

### Phase 2 — Multi-Snapshot Time-Series Tracking

#### Snapshot Registry (Step 2.1)
- [x] `parse_snapshot_date()` — regex-based filename date extraction
- [x] ISO format support: `YYYY-MM-DD` anywhere in filename
- [x] Month-DD-YYYY format support: `Jan-15-2024` (M1's download naming convention)
- [x] Returns `None` gracefully when no date found
- [x] `load_snapshots()` — builds date-keyed `dict[str, pd.DataFrame]`
- [x] Duplicate date detection with descriptive `ValueError`
- [x] Snapshots sorted ascending by date

#### Timeline Chart (Step 2.2)
- [x] `plot_portfolio_timeline()` — line chart of total portfolio value across dates
- [x] Markers at each snapshot point, hover showing date and dollar value
- [x] Consistent `ACCENT` color, `BASE_LAYOUT` applied

#### Position Delta View (Step 2.3)
- [x] `plot_position_delta()` — dual-axis line chart per symbol
- [x] Left axis: current value ($) in `ACCENT` blue
- [x] Right axis: portfolio weight (%) in `MUTED` gray, dashed
- [x] Handles symbols missing from some snapshots (sparse data)
- [x] Ticker dropdown (`st.selectbox`) in the Position Trend tab

#### Snapshot Comparison Table (Step 2.4)
- [x] `snapshot_diff()` — outer merge of oldest vs newest snapshot
- [x] Three status tags: `held`, `new`, `closed`
- [x] Delta columns: `value_change`, `return_change_pp`, `weight_change_pp`
- [x] Three sub-tables rendered with appropriate column selection and formatting
- [x] Date range caption showing comparison span
- [x] Multi-file uploader (replaces single-file uploader for Phase 2 mode)
- [x] Date picker per uploaded file with auto-populated default from filename
- [x] App correctly branches Phase 1 vs Phase 2 on `len(uploaded_files)`

#### Phase 2 Test Coverage
- [x] `test_parse_date_from_prefix()`, `test_parse_date_embedded()`, `test_parse_date_none()`
- [x] `test_load_snapshots_count_and_order()`
- [x] `test_snapshot_diff_held()`, `test_snapshot_diff_new()`, `test_snapshot_diff_closed()`
- [x] `test_snapshot_diff_value_change()`
- [x] `test_plot_portfolio_timeline_returns_figure()`
- [x] `test_plot_position_delta_held_symbol()`, `test_plot_position_delta_closed_symbol()`

---

### Phase 3 — Heatmap Landing Redesign

#### Benchmark Overlay on Portfolio Timeline
- [x] Added `requirements-optional.txt` with `yfinance>=0.2` pinned
- [x] Added guarded `yfinance` import and `fetch_benchmark()` function to `core/loader.py`
- [x] Added `YELLOW` color constant to `charts/chart_engine.py`
- [x] Extended `plot_portfolio_timeline()` with an optional `benchmarks` dict parameter
- [x] Wired opt-in checkbox and SPY/QQQ multiselect into the Timeline tab in `app.py`
- [x] Portfolio and benchmarks normalized to % return from the first snapshot date for shared-axis comparison
- [x] App remains fully offline without `yfinance` — strictly optional dependency
- [x] Added 4 mocked benchmark tests to `tests/test_loader.py` (26 total, all passing)
- [x] Documented optional dependency in `README.md` and `CONTRIBUTING.md`

#### Sector Classification Column (Step 3.1)
- [x] Created `core/sectors.json` with a 103-ticker lookup dict (S&P 500 + common ETFs + portable coverage)
- [x] Added `import json` and `from pathlib import Path` to `core/loader.py`
- [x] Added module-level sector loader: `_SECTORS_PATH`, `_SECTOR_MAP`, and `_get_sector()` helper after the `PLAIN_NUMERIC` constant
- [x] Added `df["sector"] = df["symbol"].map(_get_sector)` as the second derived column in `load_m1_csv()`
- [x] Smoke test validates ASML → Electronic Technology, GOOG → Technology Services, MA → Finance, unmapped → Other

---

## Work In Progress

> Ordered by safe, methodical development sequence. Each item builds on or is
> independent of the previous. Phase 3 items should be completed before Phase 4 begins.

### Phase 3 — Heatmap Landing Redesign

> Six gated Claude Code prompts replacing the original mini-cards-plus-radar concept.
> The radar chart concept survives as its own tab; the heatmap becomes the primary landing
> visualization. Each step ships, smoke-tests, and gates the next prompt — no queuing.

#### 3.1 — Sector Classification Column ✅ Complete
> See Work Completed for details.

#### 3.2 — Snapshot Change Computation
- [ ] Add `compute_snapshot_change(snapshots: dict) -> dict` to `core/loader.py`
- [ ] Return dict with `delta_dollar`, `delta_pct`, `days_elapsed`, `positions_added`, `positions_closed`
- [ ] Pure function: no UI, no plotting, no I/O
- [ ] Handle position-set mismatches gracefully (new and closed positions between snapshots)
- [ ] Smoke test validates returned dict shape against known two-snapshot input
- [ ] Hard constraint: no changes to `chart_engine.py` or `app.py`

#### 3.3 — Heatmap Chart Function
- [ ] Add `plot_heatmap(df) -> go.Figure` to `charts/chart_engine.py`
- [ ] Plotly treemap with positions grouped by the `sector` column
- [ ] Size by `current_value`, color by `unrealized_gain_pct`
- [ ] Reuses existing palette constants (`BASE_LAYOUT`, `PALETTE`)
- [ ] Smoke test renders the figure standalone and verifies the trace type
- [ ] Hard constraint: no changes to `loader.py`

#### 3.4 — New Landing Layout
- [ ] Replace the existing 6-card metric strip with a 5-card strip in `app.py`:
  Total Value · Gain/Loss · Snapshot Change · Positions · Best Performer
- [ ] Render `plot_heatmap()` above existing tabs as the primary landing view
- [ ] Demote the raw holdings table to a collapsible expander below the heatmap
- [ ] Add "Overview" as the new default tab pointing to the heatmap landing
- [ ] All 10 existing tab functions stay untouched
- [ ] Visual review against the agreed mockup before merging

#### 3.5 — Click-to-Detail Panel
- [ ] Wire `st.plotly_chart(on_select="rerun")` to capture heatmap tile clicks — no new dependencies
- [ ] Add `charts/detail_panel.py` with per-position visualization functions
- [ ] Detail panel renders: value-over-time line, cost basis trend, snapshot-to-snapshot quantity changes
- [ ] Panel uses only CSV-derivable data — no external calls
- [ ] Click outside the panel closes it

#### 3.6 — Responsiveness Pass (Scoped)
- [ ] KPI strip wraps cleanly across breakpoints: 5 → 3×2 → 2×3 → 1×5
- [ ] Heatmap maintains readable tile sizes down to 480px viewport
- [ ] Scope strictly limited to the new dashboard area; do not touch existing tab visualizations
- [ ] Visual review at three breakpoints (1920px, 1024px, 480px)

---

### Phase 4 — Concentration Metrics

> Promoted from the original Phase 3 scope. Adds a numeric concentration view that complements
> the heatmap's visual allocation read with HHI, top-N weight, and weight distribution.

#### 4.1 — Concentration Metrics Tab

- [ ] Compute HHI in `core/loader.py` or as a standalone utility
  - `hhi(df)` → float on scale 0–10,000 (10,000 = one position, 10,000/n = equal weight)
  - Implement alongside the existing radar `diversification` score for consistency
- [ ] Compute `top_n_weight(df, n)` → float (cumulative % of portfolio in top N positions)
- [ ] New chart function: `plot_weight_histogram(df)` → `go.Figure`
  - Histogram of portfolio weight percentages across all positions
  - Bin width configurable or automatic
- [ ] Add "Concentration" tab to single-snapshot mode
  - HHI score card with interpretation label (diversified / moderate / concentrated)
  - `st.slider` for N in top-N weight; metric updates reactively
  - Weight histogram chart below
- [ ] Add concentration metric tests

---

### Phase 5 — Packaging and Distribution

#### 5.1 — Dockerfile

- [ ] Write `Dockerfile` targeting Python 3.12-slim
- [ ] `COPY requirements.txt .` and `RUN pip install` in a separate layer for cache
- [ ] `EXPOSE 8501` and `HEALTHCHECK`
- [ ] `CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]`
- [ ] Test locally: `docker build` and `docker run -p 8501:8501`
- [ ] Add `.dockerignore` excluding `venv/`, `data/`, `*.csv`, `.git`
- [ ] Document Docker usage in `README.md`

#### 5.2 — pyproject.toml and PyPI

- [ ] Replace `requirements.txt` with `pyproject.toml`
  - `[project]` metadata: name, version, description, authors, license, classifiers
  - `[project.dependencies]`: same pins as current `requirements.txt`
  - `[project.optional-dependencies]`: `benchmarks = ["yfinance>=0.2"]`
  - `[project.scripts]`: `m1kit = "app:main"` (wrap `app.py` in a callable)
- [ ] Test `pip install -e .` locally
- [ ] GitHub Actions release workflow: on tag push → `build` + `twine upload`
- [ ] Test PyPI publish to TestPyPI first
- [ ] Document `pip install m1-portfolio-kit && m1kit` in `README.md`

#### 5.3 — Final Pre-Launch Cleanup

- [ ] Final README pass: hero screenshot, badges (CI, PyPI, license), feature table
- [ ] Final `CONTRIBUTING.md` pass: Docker workflow, optional dependency notes
- [ ] Convert `work-in-progress.md` content into final README sections
- [ ] Add GitHub issue templates: bug report, feature request
- [ ] Tag `v1.0.0` release on GitHub
- [ ] Verify CI badge is green on main branch

---

## Future Improvements

> Ten concepts ranked by a combination of user value, feasibility, and strategic impact.
> These are outside the current roadmap and require separate scoping decisions.

---

### 1. AI-Powered Portfolio Health Digest

Integrate a lightweight LLM call (Claude API, local Ollama, or optional OpenAI key) to
generate a one-paragraph natural language summary of the portfolio after each CSV upload.
The digest would summarize top performers, concentration risk, benchmark comparison if
available, and one actionable observation. Critically, no holdings data would ever leave
the machine unless the user explicitly enables a cloud LLM provider — a local model via
Ollama is the privacy-preserving default. This transforms the tool from a chart viewer
into an analyst in a box, dramatically increasing its perceived value for non-technical
M1 users who have the data but not the vocabulary to interpret it.

---

### 2. PDF Snapshot Report Generator

A one-click export button that produces a PDF containing all rendered charts, the summary
metrics, and the AI digest (if enabled) — formatted as a professional portfolio review
document. Uses `WeasyPrint` or `reportlab` to render charts to a printable layout. The
PDF is generated entirely locally and saved to the user's `Downloads` folder. This
opens a personal finance record-keeping use case: users who want a dated audit trail of
their portfolio state without screenshotting tabs manually. The PDF becomes the
product's physical artifact — something users share with a financial advisor or store
with tax documents.

---

### 3. Goal Allocation Tracker with Drift Alerts

Allow users to define a target allocation — either as a simple text input (e.g., `AAPL
30%, MSFT 20%`) or by uploading a `target_allocation.csv` — and overlay a drift
visualization on the allocation donut. A secondary tab shows each position's current
weight versus target weight, colored by drift severity (within tolerance, approaching
limit, breached). M1's auto-invest feature already rebalances toward targets, but it
never shows you how far from target you are right now. This feature fills that gap and
gives M1's pie-based investing philosophy the visual feedback it deserves.

---

### 4. Portfolio Stress Test Simulator

Using historical price data fetched via `yfinance` (the same infrastructure as the
benchmark overlay), model how the current portfolio would have performed during
user-selectable historical stress events: 2020 COVID crash, 2022 rate hike cycle,
2008 financial crisis, etc. The simulator applies the historical percentage drawdown
of each held ticker during the selected event window to the current holdings and
renders the hypothetical outcome — showing estimated portfolio value, largest position
losses, and recovery timeline. This is not a prediction; it is a risk visualization tool
that helps investors understand concentration risk before a drawdown happens.

---

### 5. Hosted Privacy-Safe Demo (Synthetic Data Mode)

Deploy a publicly accessible Streamlit Cloud instance pre-loaded with a synthetic,
realistic-looking portfolio (no real holdings, randomized tickers with plausible values)
that allows anyone to explore the full feature set without installing Python. This
removes the single largest adoption barrier — the requirement to run a local Python
environment — for non-technical M1 users who heard about the tool from a Reddit post.
The instance is stateless (no uploads are persisted), the synthetic data makes it clear
no real holdings are present, and the deployment cost is zero via Streamlit Community
Cloud. This transforms the tool's go-to-market surface from "GitHub repo for developers"
to "web app anyone can try in 10 seconds."

---

### 6. Dividend and Income Tracking Layer

M1 currently does not include dividend history in its holdings CSV export, but it does
surface dividend data in the web interface. If M1 adds dividend export — or if users
manually supply a `dividends.csv` with `date`, `symbol`, and `amount` columns — the
application could render a dividend income timeline, yield-on-cost per position, and
annual income projection based on current holdings and trailing yield. This makes the
tool relevant to income investors, a significant subset of M1's user base who invest
in dividend-paying ETFs and whose primary question is "how much income is this portfolio
generating?" — a question M1's interface answers poorly.

---

### 7. CLI Headless Mode and Programmatic API

Expose `core/loader.py` and `charts/chart_engine.py` as a clean Python API that can be
imported and used without Streamlit. Add a CLI entry point (`m1kit analyze
holdings.csv --output report.html`) that produces a self-contained HTML file with all
charts rendered as embedded Plotly figures. This serves the secondary and tertiary
audience segments from the master plan: data-oriented investors who want to run the
analysis in a Jupyter notebook, automate it in a cron job, or integrate it into a
broader data pipeline. The Streamlit UI and the analytical core are already cleanly
separated — this improvement makes that separation explicit and public.

---

### 8. Community Sector Map Registry

Build and host a community-maintained `sector_map.csv` file on GitHub covering the most
commonly held tickers in M1 Finance portfolios (top ETFs, individual stocks, M1's own
model pies). Ship a bundled fallback sector map with the application so that sector
analysis works out of the box for typical M1 portfolios, with the user-supplied
`sector_map.csv` taking precedence for custom or less-common tickers. Establish a
GitHub contribution workflow where users can submit PRs to add missing tickers.
This dramatically improves the out-of-box experience for Phase 3's sector features
and creates a small community contribution surface that builds network effects around
the project.

---

### 9. Watchlist and Opportunity Overlay

Allow users to maintain a `watchlist.csv` of tickers they are considering but not yet
holding. The watchlist positions appear as ghost markers in the Return vs Weight bubble
chart (outlined, unfilled, labeled "watch") so the user can see how a potential addition
would change their concentration and return profile relative to existing positions.
If benchmark data is enabled, the watchlist tickers are compared against the portfolio's
existing composition, showing hypothetical weight impact. This transforms the tool from
pure retrospective analysis into a lightweight decision-support tool — answering "should
I add this to my portfolio?" with spatial and comparative context.

---

### 10. M1 Finance Browser Extension for One-Click Export

Build a lightweight browser extension (Chrome/Firefox) that adds an "Open in Portfolio
Kit" button directly to M1's Holdings page. The extension detects when the user is
viewing their holdings, automatically triggers the CSV export, pipes the downloaded
file directly to a locally running instance of M1 Portfolio Kit, and opens the
dashboard. This eliminates the entire manual export-upload workflow — the biggest
friction point in the current user journey — and makes the tool feel native to the M1
experience. The extension communicates only with `localhost:8501` and reads no account
data itself; it simply automates the button clicks the user would perform manually.
This is the highest-impact go-to-market lever available: it embeds M1 Portfolio Kit
into the M1 workflow itself and makes every M1 user a potential daily-active user.

---

*Last updated: 2026-05-22 | Phase 3.1 complete | Heatmap landing redesign in progress*
