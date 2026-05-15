# App Flow, Pages, and Roles — M1 Portfolio Kit

> Technical specification of every user-facing state, page, and interaction path.
> Phase 1 scope. All users are equal — no roles, no auth, no admin tier.

---

## 1. User Roles

**Phase 1 has exactly one role: the local user.**

There is no authentication, no server, no multi-user session management. The application
runs on `localhost`. The person who started `streamlit run app.py` is the only user.
Every Streamlit session is isolated in-memory and discarded on page refresh.

No admin role. No guest role. No API token. No login screen.

**Phase 2 note:** If the tool is eventually containerized for shared internal use (e.g.,
a team's finance server), role separation may become relevant. It is not a Phase 1
concern and will not be designed speculatively here.

---

## 2. Application Pages

Phase 1 is a single-page application (SPA). Streamlit does not use traditional routing.
All content renders in `app.py` within a single vertical scroll container.

The page has four logical sections, each conditional on state:

| Section | Renders when | Streamlit mechanism |
|---|---|---|
| Header + Uploader | Always | Static render |
| Error state | Upload fails validation | `st.error()` + `st.stop()` |
| Summary metrics row | CSV loaded successfully | `st.columns(6)` + `st.metric()` |
| Data expander | CSV loaded | `st.expander()` |
| Chart tabs | CSV loaded | `st.tabs()` + `st.plotly_chart()` |
| Footer | Always | `st.caption()` |

---

## 3. Complete User Flow

### 3.1 — App Launch

```
User runs: streamlit run app.py
Browser opens: http://localhost:8501
```

**State:** No CSV loaded.

**Renders:**
- Page title: "📈 M1 Portfolio Kit"
- Caption explaining the export path
- Horizontal divider
- File uploader widget (label: "Upload M1 Holdings CSV")
- Info box: "⬆️  Drop your M1 holdings CSV above to get started."
- Footer

**User action required:** Upload a CSV file or drag-and-drop onto the uploader widget.

---

### 3.2 — File Upload

**Trigger:** User selects or drops a `.csv` file onto the uploader.

**Streamlit behavior:** File is read into memory as a file-like object
(`st.UploadedFile`). No file is written to disk. The upload widget re-renders with
the filename displayed.

**What happens next:** `load_m1_csv(uploaded_file)` is called.

---

### 3.3a — Upload Success Path

**Condition:** File parses successfully and passes schema validation.

**Processing steps (in `loader.py`):**
1. `pd.read_csv(source)` — parse raw CSV
2. `df.dropna(how="all")` — remove M1's totals row
3. Column presence check — all eight M1 columns must be present
4. `df.rename(columns=M1_COLUMN_MAP)` — normalize to internal schema
5. `_clean_numeric()` on comma-formatted columns
6. `pd.to_numeric()` on plain numeric columns
7. `df.dropna(subset=["symbol"])` — remove any remaining summary rows
8. Derive `portfolio_weight_pct`
9. Return normalized DataFrame

**Renders (in order, top to bottom):**

#### Summary Metrics Row
Six equally-spaced cards:
```
Total Value | Total Gain / Loss | Positions | Winners 🟢 | Losers 🔴 | Best Performer
```

- "Total Value": formatted `${:,.2f}`
- "Total Gain / Loss": formatted `${:+,.2f}` with delta `{:+.2f}%`
- "Positions": integer count
- "Winners 🟢": integer count of positions with `unrealized_gain_dollar > 0`
- "Losers 🔴": integer count of positions with `unrealized_gain_dollar < 0`
- "Best Performer": ticker symbol of position with highest `unrealized_gain_pct`

#### Horizontal Divider

#### Raw Data Expander (collapsed by default)
Label: "View raw holdings data"
Contents: formatted `st.dataframe()` with the full normalized DataFrame.

#### Chart Tabs (five tabs)
Each tab contains one chart rendered via `st.plotly_chart(..., use_container_width=True)`.

| Tab | Label | Chart function | Question answered |
|---|---|---|---|
| 1 | 🥧  Allocation | `plot_allocation(df)` | What percentage of my portfolio is each position? |
| 2 | 💵  Gain / Loss ($) | `plot_gainloss_dollar(df)` | Which positions are making or losing me the most dollars? |
| 3 | 📊  Gain / Loss (%) | `plot_gainloss_pct(df)` | Which positions have the best/worst return rate, regardless of size? |
| 4 | ⚖️  Cost vs Value | `plot_cost_vs_value(df)` | What did I pay vs what is it worth now? |
| 5 | 🎯  Return vs Weight | `plot_return_vs_weight(df)` | Are my biggest positions also my best performers? |

#### Footer
```
m1-portfolio-kit · Open source · Data never leaves your machine · GitHub
```

---

### 3.3b — Upload Error Path (Schema Validation Failure)

**Condition:** The uploaded CSV is missing one or more of the eight required M1 columns.

**What renders:**
- `st.error()` box with:
  - Bold header: "**Could not parse your CSV.**"
  - Body: the `ValueError` message listing which columns are missing and what columns
    were found
- `st.stop()` — nothing below this renders
- File uploader remains visible; user can upload a different file

**Recovery:** User uploads a correctly-exported M1 CSV.

---

### 3.3c — Upload Error Path (Unexpected Exception)

**Condition:** Any exception other than `ValueError` raised during `load_m1_csv()`.

**What renders:**
- `st.error()` box with:
  - "**Unexpected error loading file:** {str(exception)}"
- `st.stop()`

**Recovery:** User can retry or report the error as a GitHub issue.

---

### 3.4 — Chart Interaction

Once the dashboard renders, the user interacts with Plotly charts.

**Available interactions (Plotly native, no custom code needed):**

| Interaction | How | Effect |
|---|---|---|
| Hover | Mouse over any chart element | Tooltip with full position data |
| Zoom | Click-drag on chart area | Zooms into selected region |
| Pan | Click chart toolbar → pan tool, then drag | Pans across zoomed view |
| Reset zoom | Double-click on chart | Returns to full extent |
| Toggle series | Click legend item (chart 4 only) | Shows/hides Cost Basis or Current Value |
| Download PNG | Click camera icon in Plotly toolbar | Saves chart as PNG |

**No custom click handlers in Phase 1.** Charts are read-only; clicking a slice or bar
does nothing beyond Plotly's default selection highlight.

---

### 3.5 — Raw Data Table Interaction

The expander "View raw holdings data" is collapsed by default.

**Expand:** Click the expander header.
**Collapse:** Click again.
**Contents:** Full normalized DataFrame with formatted columns.

Streamlit's built-in `st.dataframe` provides:
- Column sorting (click any header)
- Horizontal scroll if viewport is narrow
- Row hover highlight

---

### 3.6 — Refresh / New Upload

**User wants to analyze a different CSV:**
- Upload a new file via the same uploader widget
- Streamlit reruns the entire script from top with the new file
- No state persists between uploads

**User refreshes the browser:**
- All in-memory state is cleared
- App returns to the empty uploader state (Step 3.1)

---

## 4. Page State Machine

```
[APP LAUNCH]
     │
     ▼
[EMPTY STATE] ──── user uploads CSV ────► [LOADING]
     ▲                                        │
     │                                   ┌────┴────┐
     │                                   │         │
     │                              [SUCCESS]   [ERROR]
     │                                   │         │
     │                              [DASHBOARD]  [ERROR BOX]
     │                                   │    + [UPLOADER]
     └───── refresh / new upload ─────────┘
```

---

## 5. URL and Routing

**Phase 1:** Single route only — `http://localhost:8501/`

No query parameters. No deep linking. No URL state.

**Phase 2 consideration:** Streamlit's `st.experimental_get_query_params()` could be
used to pass a snapshot date as a URL parameter for shareable views. Not designed or
implemented in Phase 1.

---

## 6. Session State

Streamlit reruns the entire `app.py` script on every user interaction. In Phase 1,
no `st.session_state` is used — the DataFrame is recomputed on every rerun from the
uploaded file, which Streamlit caches in the uploader widget for the duration of the
browser session.

**Phase 2** will require `st.session_state` to hold the snapshot registry (list of
DataFrames) across reruns when multiple files are uploaded.

---

## 7. Accessibility Notes

- Color-encoded bars (GREEN/RED) always display a labeled value on hover — colorblind
  users retain context via the number, not just the color.
- All charts include axis titles and chart titles in the rendered figure.
- Tab labels include descriptive emoji + text — screen reader friendly with Streamlit's
  default tab implementation.
- No ARIA customization is applied in Phase 1; Streamlit's native accessibility is
  the baseline.

---

## 8. Phase 2 Page Additions (Planned, Not Built)

When Phase 2 ships, the following additions will be made to this document:

| New element | Description |
|---|---|
| Multi-file uploader | Replaces single-file uploader; accepts multiple CSVs |
| Snapshot date inputs | Date picker or filename-parsed date per uploaded file |
| New tab: 📅  Timeline | Portfolio value over time (line chart) |
| New tab: 🔄  Snapshot Diff | Position-level delta between oldest and newest snapshot |
| Ticker dropdown | Select a position to view its cross-snapshot trend |

No Phase 2 UI elements are present in the Phase 1 codebase.
