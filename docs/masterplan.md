# masterplan.md — M1 Portfolio Kit

> High-level blueprint for an open-source, privacy-first portfolio visualization tool
> built on Python, pandas, Streamlit, and Plotly for M1 Finance users.

---

## 1. App Overview and Objectives

**What it is:** A local-only, open-source web application that transforms M1 Finance
holdings CSV exports into interactive, analyst-grade portfolio visualizations.

**Why it exists:** M1 Finance's native interface surfaces basic numbers but offers
minimal charting depth. Users who want to understand position-level performance,
concentration risk, return attribution, and portfolio composition over time have no
good tool that (a) respects their privacy and (b) works with M1's native export format.

**Core promise:** Drop in your CSV → get charts M1 doesn't give you → your data never
leaves your machine.

**Primary success metric:** A user can go from CSV export to insight in under 60 seconds
with zero configuration.

---

## 2. Target Audience

| Segment | Description |
|---|---|
| Primary | M1 Finance retail investors who are moderately tech-literate (comfortable running a Python app locally or via Docker) |
| Secondary | Data-oriented investors who want to inspect holdings programmatically and extend the tool |
| Tertiary | Python/pandas learners who want a real-world, approachable open-source codebase to study and contribute to |

**Non-target:** Enterprise users, financial advisors, anyone expecting brokerage connectivity
or live price feeds.

---

## 3. Core Features by Phase

### Phase 1 — Single Snapshot Analysis (current)
- CSV ingestion with schema validation and normalization
- Portfolio summary metrics: total value, gain/loss, winners/losers, best/worst
- Five interactive Plotly charts:
  1. Allocation donut — portfolio weight by current value
  2. Gain/Loss ($) — unrealized dollar gain per position
  3. Gain/Loss (%) — unrealized return % per position
  4. Cost vs Value — side-by-side bar per position
  5. Return vs Weight — scatter/bubble: are big positions also good ones?
- Raw data table with formatted display
- Dark-mode-first UI matching M1's terminal aesthetic

### Phase 2 — Multi-Snapshot Time-Series Tracking
- Upload multiple CSVs (dated snapshots)
- Portfolio total value over time (line chart)
- Position-level entry/exit tracking across snapshots
- New metric: portfolio growth rate between snapshots

### Phase 3 — Benchmark Comparison and Risk Views
- Compare portfolio return against SPY, QQQ, or a custom benchmark
- Concentration metrics: Herfindahl-Hirschman Index, top-N weight
- Drawdown and volatility views (requires enough snapshots)
- Sector/asset class breakdown (requires a mapping layer)

### Phase 4 — Community and Distribution
- Docker image for zero-install startup
- GitHub Actions CI (lint + smoke test on every PR)
- Contribution guide and issue templates
- Potential PyPI package for `pip install m1-portfolio-kit`

---

## 4. High-Level Technical Stack

| Layer | Choice | Rationale |
|---|---|---|
| UI runtime | Streamlit | Zero-boilerplate web UI for data apps; no JS required |
| Charting | Plotly (graph_objects) | Full control over traces, hover, layout; interactive by default |
| Data layer | pandas + NumPy | Industry standard; aligns with developer's learning goals |
| Language | Python 3.10+ | Broadest compatibility; f-string support; modern type hints |
| Packaging | pip + requirements.txt | Simplest for open-source onboarding; Docker added in Phase 4 |
| Version control | Git + GitHub | Standard; enables open-source collaboration |

**No backend, no database, no auth service.** All state lives in-memory during a session.
Files are user-supplied and never transmitted.

---

## 5. Conceptual Data Model

### Normalized Holdings DataFrame (Phase 1)
All chart functions operate on a single normalized DataFrame produced by `core/loader.py`.

| Column | Type | Source |
|---|---|---|
| `symbol` | str | M1 raw: Symbol |
| `name` | str | M1 raw: Name |
| `quantity` | float | M1 raw: Quantity |
| `avg_price` | float | M1 raw: Avg. Price |
| `cost_basis` | float | M1 raw: Cost Basis |
| `unrealized_gain_dollar` | float | M1 raw: Unrealized Gain ($) |
| `unrealized_gain_pct` | float | M1 raw: Unrealized Gain (%) |
| `current_value` | float | M1 raw: Value |
| `portfolio_weight_pct` | float | Derived: current_value / total × 100 |

### Phase 2 Extension — Snapshot Registry
A dict or lightweight SQLite table keyed by snapshot date, containing one normalized
DataFrame per export. No schema changes to the core DataFrame.

---

## 6. User Interface Design Principles

1. **Dark-first, always.** The color system (`#0d1117` background, `#e6edf3` text,
   `#58a6ff` accent) is fixed — no light mode in Phase 1.
2. **Data density without clutter.** Monospace fonts for metrics; charts fill the full
   container width; tabs prevent scroll fatigue.
3. **Zero configuration UX.** The app asks for exactly one thing: the CSV. Every chart
   renders automatically from that single input.
4. **Hover is the detail layer.** Chart annotations stay minimal; hover tooltips surface
   full position data without crowding the canvas.
5. **Accessible defaults.** Green/red color encoding is always paired with a label or
   value so colorblind users retain context.

---

## 7. Security Considerations

- No network requests in Phase 1. The app is entirely offline-capable.
- CSV files are read into memory and discarded when the session ends — Streamlit's
  `st.file_uploader` does not persist uploads to disk.
- `.gitignore` explicitly excludes the `data/` directory and all `*.csv` files.
- No credentials, API keys, or account tokens are collected or required.
- Phase 2+ will maintain the same local-only constraint unless the user explicitly
  opts into an external data source.

---

## 8. Development Phases and Milestones

| Phase | Milestone | Definition of Done |
|---|---|---|
| 1 | Scaffold + 5 charts | Smoke test passes; app runs from a single CSV upload |
| 1 | Open-source release | README complete; repo public; CI badge present |
| 2 | Multi-CSV ingestion | User can upload N files; portfolio value timeline renders |
| 2 | Snapshot diffing | Position-level delta between two dates visible |
| 3 | Benchmark overlay | SPY/QQQ comparison line on timeline chart |
| 3 | Concentration metrics | HHI, top-5 weight, sector breakdown |
| 4 | Docker packaging | `docker run` brings up the app with no Python install |
| 4 | PyPI distribution | `pip install m1-portfolio-kit && m1kit` works |

---

## 9. Potential Challenges and Mitigations

| Challenge | Mitigation |
|---|---|
| M1 changes their CSV export format | Schema validation in `loader.py` surfaces the mismatch immediately with a clear error message; column map is isolated and easy to patch |
| Large portfolios with 50+ positions cause chart overcrowding | Add a configurable top-N filter per chart in Phase 1.x; default to showing all |
| Multi-CSV date parsing (Phase 2) | Require ISO date in filename or a date picker; never guess |
| Pandas learning curve for contributors | Keep logic in `loader.py` heavily commented; add a dev guide |
| Streamlit version drift | Pin major version in requirements.txt; test on upgrade |

---

## 10. Future Expansion Possibilities

- **Dividend tracking** — if M1 ever exports dividend history, a yield-on-cost view
- **Goal tracking** — user sets a target allocation; app shows drift
- **PDF report export** — one-page snapshot summary for personal records
- **Watchlist overlay** — positions not yet owned but tracked
- **Community themes** — light mode, high-contrast, alternate color palettes
- **Pie aggregation mode** — group by sector/asset class when a mapping CSV is provided
