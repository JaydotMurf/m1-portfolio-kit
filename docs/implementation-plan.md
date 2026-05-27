# Implementation Plan — M1 Portfolio Kit

> Ordered development roadmap prioritizing: working software first, scalability second,
> zero unnecessary complexity throughout. Each phase ships independently.

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| **Phase 1** | ✅ Complete | All steps 1.1–1.7 done. Recent UX polish: dark-only theme, table color coding, title-case headers. |
| **Phase 2** | ✅ Complete | All steps 2.1–2.4 done. Multi-CSV time-series tracking fully functional. |
| **Phase 3** | ✅ Complete | Heatmap landing, click-to-detail, benchmark overlay, sector classification, responsiveness. |
| **Phase 4** | ⏳ Not designed | Containerization and package distribution. Deferred until shipping is needed. |

---

## Guiding Principles

1. **Phase 1 must be fully usable before Phase 2 begins.** No half-built multi-CSV
   infrastructure bleeding into single-snapshot code.
2. **Every addition is tested with a synthetic CSV** before touching real holdings data.
3. **`loader.py` is the seam.** All format concerns live there. Charts never parse strings.
4. **If a feature requires a new package, it gets flagged, justified, and added to
   `requirements.txt` explicitly** — never installed quietly.
5. **No premature abstraction.** Add indirection only when a third repetition demands it.

---

## Phase 1 — Single Snapshot Analysis

**Goal:** A user uploads one M1 CSV and gets five interactive charts and a summary header.
**Definition of done:** Smoke test passes. App runs locally. Repo is public.

---

### Step 1.1 — Project Scaffold ✅
**What:** Directory structure, virtual environment, git init.
**Files produced:**
- `app.py`
- `core/__init__.py`, `core/loader.py`
- `charts/__init__.py`, `charts/chart_engine.py`
- `requirements.txt`, `.gitignore`, `README.md`, `data/.gitkeep`

**Validation:** `python -c "from core.loader import load_m1_csv"` runs without error.

---

### Step 1.2 — CSV Ingestion and Normalization ✅
**What:** `load_m1_csv()` in `core/loader.py`.
**Responsibilities:**
- Read raw M1 CSV via `pd.read_csv()`
- Drop fully-empty rows (M1 appends a totals row)
- Validate all required M1 column names are present; raise `ValueError` with a clear
  message if not
- Rename columns to internal snake_case schema via `M1_COLUMN_MAP`
- Strip comma formatting and `$` signs from currency columns
- Cast all numeric columns to float; coerce unparseable values to NaN
- Drop rows where `symbol` is NaN (catches summary rows M1 sometimes includes)
- Derive `portfolio_weight_pct` = `current_value / total_value * 100`

**Validation:** Smoke test asserts 3 rows, correct column names, correct winner/loser count.

---

### Step 1.3 — Portfolio Summary Metrics ✅
**What:** `portfolio_summary()` in `core/loader.py`.
**Returns:** flat dict with:
- `total_value`, `total_cost`, `total_gain`, `total_return_pct`
- `positions`, `winners`, `losers`
- `largest_position`, `best_performer`, `worst_performer`

**Used by:** `app.py` metric row (six `st.metric()` cards).

---

### Step 1.4 — Five Core Charts ✅
**What:** Five functions in `charts/chart_engine.py`, each accepting the normalized
DataFrame and returning a `go.Figure`.

| Function | Chart Type | Key Columns |
|---|---|---|
| `plot_allocation` | Donut (Pie with hole) | `symbol`, `current_value` |
| `plot_gainloss_dollar` | Horizontal bar | `symbol`, `unrealized_gain_dollar`, `unrealized_gain_pct` |
| `plot_gainloss_pct` | Horizontal bar | `symbol`, `unrealized_gain_pct`, `unrealized_gain_dollar` |
| `plot_cost_vs_value` | Grouped vertical bar | `symbol`, `cost_basis`, `current_value` |
| `plot_return_vs_weight` | Scatter/bubble | `portfolio_weight_pct`, `unrealized_gain_pct`, `current_value` |

All charts share `BASE_LAYOUT` (dark background, monospace font, grid color).
Green/red encoding uses `GREEN = "#3fb950"` / `RED = "#f85149"` consistently.

---

### Step 1.5 — Streamlit App Shell ✅
**What:** `app.py` wires everything together.
**Layout:**
- Page config: wide layout, dark favicon
- CSS injection: card styling for metrics, tab accent color
- File uploader → loader → summary metrics → raw data expander → tabbed charts

**Error handling:**
- `ValueError` from `load_m1_csv` → `st.error()` with the validation message
- Unexpected exceptions → `st.error()` with raw message
- No file uploaded → `st.info()` prompt, then `st.stop()`

---

### Step 1.6 — Smoke Test and CI ✅
**What:** Automated test that runs on every push.
**Status:** Test coverage in place; CI workflow configured.

---

### Step 1.7 — README and Open-Source Release ✅
**What:** Final README pass + repo goes public.
**Status:** Complete. README includes setup, feature overview, M1 export instructions, and contribution guide.

---

## Phase 2 — Multi-Snapshot Time-Series Tracking ✅

**Goal:** Upload multiple CSVs (one per export date) and see portfolio value over time.
**Status:** All steps 2.1–2.4 complete and tested.

---

### Step 2.1 — Snapshot Registry ✅
**What:** `load_snapshots(files: list, date_map: dict) -> dict[str, pd.DataFrame]` in `core/loader.py`.
**Status:** Complete. Handles ISO date parsing (YYYY-MM-DD), Month-DD-YYYY format, and date picker fallback.

---

### Step 2.2 — Timeline Chart ✅
**What:** `plot_portfolio_timeline(snapshots: dict) -> go.Figure` in `chart_engine.py`.
**Status:** Complete. Line chart shows total portfolio value across snapshot dates.

---

### Step 2.3 — Position Delta View ✅
**What:** `plot_position_delta(snapshots: dict, symbol: str) -> go.Figure` in `chart_engine.py`.
**Status:** Complete. Dropdown in `app.py` selects ticker; chart updates reactively showing value and weight trends.

---

### Step 2.4 — Snapshot Comparison Table ✅
**What:** New tab "🔄 Snapshot Diff" in `app.py`.
**Status:** Complete. Shows held positions (with deltas), new positions, and closed positions between oldest and newest snapshot.

---

## Phase 3 — Benchmark Comparison and Risk Views ⏳

**Status:** Designed, ready to build. No work started yet.

**Three additions planned:**

1. **Benchmark overlay on timeline chart**
   - Shows SPY and/or QQQ performance alongside portfolio value
   - Requires external data fetch via `yfinance` (opt-in, clearly labeled as network call)
   - Date range must match snapshot dates
   - Will add `requirements-optional.txt` for optional dependencies

2. **Concentration metrics tab**
   - **HHI (Herfindahl-Hirschman Index)** — single number 0–10,000 (perfect diversity = 2,500)
   - **Top-N weight** — cumulative % of portfolio in top 5/10 positions
   - **Weight distribution histogram** — visual representation of concentration across all positions
   - Interactive: slider to adjust N

3. **Sector mapping**
   - User uploads `sector_map.csv` with columns: `symbol`, `sector`
   - Donut chart breaks down portfolio by sector (not just by position)
   - Sector diffs in snapshot comparison (new sectors, closed sectors)
   - No hardcoded sector assumptions; user-defined mappings only

**Implementation order:** Likely 1 → 2 → 3 (benchmarks require data layer; concentration is pure calculation; sectors require mapping infrastructure)

---

## Phase 4 — Packaging and Distribution

**Anticipated additions:**
- `Dockerfile` for zero-Python-install startup
- PyPI package: `pip install m1-portfolio-kit`
- `pyproject.toml` replacing `requirements.txt` for proper packaging
- GitHub release workflow with changelog generation

---

## Dependency Management Rules

| Trigger | Action |
|---|---|
| New chart type needs a new library | Flag in PR, add to `requirements.txt`, update README |
| Phase 2 needs date parsing | `python-dateutil` — already a pandas transitive dep, no install needed |
| Phase 3 needs benchmark data | Explicit opt-in flag; `yfinance` or similar added to a separate `requirements-optional.txt` |
| Testing infrastructure | `pytest` added to `requirements-dev.txt`, not `requirements.txt` |

---

## What Is Explicitly Out of Scope

| Item | Reason |
|---|---|
| Live price feeds (Phase 1) | Breaks the local-only privacy guarantee |
| User authentication | No server, no accounts, no need |
| Multi-user or SaaS deployment | Out of scope for all phases |
| Brokerage API connectivity | Complexity without proportional value; M1's CSV export is sufficient |
| Hardcoded tickers or portfolio assumptions | Tool must work for any M1 user |
