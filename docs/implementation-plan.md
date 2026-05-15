# Implementation Plan — M1 Portfolio Kit

> Ordered development roadmap prioritizing: working software first, scalability second,
> zero unnecessary complexity throughout. Each phase ships independently.

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

### Step 1.6 — Smoke Test and CI *(next)*
**What:** Automated test that runs on every push.
**Test file:** `tests/test_loader.py`
**Covers:**
- Happy path: 3-row synthetic CSV → correct shape, columns, derived values
- Missing column: raises `ValueError` with column name in message
- Comma-formatted currency: parsed correctly
- Negative gain: `losers` count correct
- All five chart functions: return non-None `go.Figure`

**CI:** GitHub Actions workflow (`.github/workflows/smoke.yml`)
- Trigger: push to `main`, PRs
- Steps: `pip install -r requirements.txt` → `pytest tests/`

---

### Step 1.7 — README and Open-Source Release *(next)*
**What:** Final README pass + repo goes public.
**README must include:**
- One-command setup block
- Screenshot or GIF of the running app
- M1 CSV export instructions (step-by-step)
- Contribution guide link

---

## Phase 2 — Multi-Snapshot Time-Series Tracking

**Goal:** Upload multiple CSVs (one per export date) and see portfolio value over time.
**Constraint:** Phase 1 behavior is unchanged. Multi-CSV is additive, not a rewrite.

---

### Step 2.1 — Snapshot Registry
**What:** A new function `load_snapshots(files: list) -> dict[str, pd.DataFrame]`
in `core/loader.py`.
**Behavior:**
- Accepts a list of uploaded files
- Extracts the snapshot date from the filename (format: `YYYY-MM-DD_m1_holdings.csv`)
  or falls back to a date picker per file
- Returns an ordered dict: `{date_str: normalized_df}`

**No changes to existing `load_m1_csv()` — it is called internally per file.**

---

### Step 2.2 — Timeline Chart
**What:** `plot_portfolio_timeline(snapshots: dict) -> go.Figure` in `chart_engine.py`.
**Columns used:** Derived — `total_value` per snapshot date (from `portfolio_summary()`).
**Chart type:** Line chart with markers; x = date, y = total portfolio value.

---

### Step 2.3 — Position Delta View
**What:** `plot_position_delta(snapshots: dict, symbol: str) -> go.Figure`
**Shows:** `current_value` and `portfolio_weight_pct` for a single ticker across dates.
**UI:** Dropdown in `app.py` to select the ticker; chart updates reactively.

---

### Step 2.4 — Snapshot Comparison Table
**What:** A new tab "📅 Snapshot Diff" in `app.py`.
**Shows:** For each position present in both the oldest and newest snapshot:
- Value change ($), Return change (%), Weight change (pp)
- New positions (appeared in latest), Closed positions (missing from latest)

---

## Phase 3 — Benchmark Comparison and Risk Views

> Phase 3 is planned but not yet designed in detail. Design begins when Phase 2 ships.

**Anticipated additions:**
- Benchmark overlay on timeline chart (SPY/QQQ — requires external data; will be
  opt-in and clearly flagged as a network call)
- Concentration metrics tab: HHI, top-N weight, weight distribution histogram
- Sector mapping via a user-supplied `sector_map.csv` (no hardcoded assumptions)

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
