# Design Guidelines — M1 Portfolio Kit

> A complete design token specification and component rulebook.
> All values are implementation-ready for Streamlit CSS injection and Plotly layout dicts.

---

## 1. Design Philosophy

**Terminal-grade financial UI.** The aesthetic is deliberate: a developer's Bloomberg
terminal, not a consumer fintech app. Dark background, monospace data, high-contrast
signal colors. Every design decision serves legibility of financial data, not decoration.

**Four rules:**
1. Data is the hero. UI chrome stays minimal.
2. Color carries meaning. Green = gain. Red = loss. Blue = neutral/accent. Never use
   these colors for decoration.
3. Hover is the detail layer. Charts stay uncluttered; tooltips reveal full context.
4. No light mode in Phase 1. Dark-first is a feature, not a limitation.

---

## 2. Color System

### Background Palette

| Token | Hex | Usage |
|---|---|---|
| `BG` | `#0d1117` | Page background, chart plot area |
| `PAPER` | `#0d1117` | Plotly paper background (same as BG for seamless charts) |
| `SURFACE` | `#161b22` | Metric cards, expandable panels, tooltip backgrounds |
| `BORDER` | `#21262d` | Card borders, grid lines, dividers, zero-lines on charts |
| `SURFACE_HOVER` | `#1c2128` | Card hover state, row hover in data table |

### Text Palette

| Token | Hex | Usage |
|---|---|---|
| `TEXT` | `#e6edf3` | Primary text, chart labels, metric values |
| `MUTED` | `#8b949e` | Secondary labels, captions, axis titles, zero-line markers |
| `DISABLED` | `#484f58` | Placeholder text, empty states |

### Signal Colors

| Token | Hex | Usage |
|---|---|---|
| `GREEN` | `#3fb950` | Positive gain (bars, scatter markers, metric deltas) |
| `RED` | `#f85149` | Negative loss (bars, scatter markers, metric deltas) |
| `ACCENT` | `#58a6ff` | Current value bars, links, selected tab underline, info states |
| `YELLOW` | `#d29922` | Warning states, breakeven / near-zero positions |

**Rule:** GREEN and RED are never used for decoration. A bar is green because the position
is profitable. A metric delta is red because the portfolio is down. No exceptions.

### Chart Color Palette (multi-series)

For charts that need distinct colors per symbol (e.g., donut, future grouped lines),
use Plotly's `T10` qualitative palette, applied in value-descending order:

```
px.colors.qualitative.T10
```

This gives 10 distinct, accessible colors. If a portfolio exceeds 10 positions, colors
cycle — acceptable for Phase 1 since the donut is the only multi-color chart.

---

## 3. Typography

### Font Stack

| Role | Family | Fallback |
|---|---|---|
| All UI text | `"monospace"` | system monospace |
| Plotly charts | `"monospace"` | system monospace |
| Streamlit body | Inherited from Plotly theme injection | — |

**Rationale:** Monospace aligns decimal points, percentage signs, and dollar amounts
without variable-width rendering artifacts. It reinforces the terminal aesthetic.
Streamlit's default sans-serif is overridden via CSS injection in `app.py`.

### Type Scale

| Role | Size | Weight | Color |
|---|---|---|---|
| App title (`st.title`) | Streamlit default (~28px) | Bold | `TEXT` |
| Section header | 14px | Bold | `TEXT` |
| Chart title | 14px | Normal | `TEXT` |
| Metric label | 12px | Normal | `MUTED` |
| Metric value | Streamlit default | Bold | `TEXT` |
| Metric delta | 13px | Normal | `GREEN` or `RED` |
| Caption / footer | Streamlit default | Normal | `MUTED` |
| Chart axis label | 12px | Normal | `MUTED` |
| Chart hover tooltip | 12px | Normal | `TEXT` |
| Data table cell | 13px | Normal | `TEXT` |
| Tab label (unselected) | Streamlit default | Normal | `MUTED` |
| Tab label (selected) | Streamlit default | Normal | `ACCENT` |

---

## 4. Spacing and Layout

### Page Layout

| Property | Value |
|---|---|
| Page width | `layout="wide"` — fills viewport |
| Sidebar | `initial_sidebar_state="collapsed"` — hidden by default |
| Top padding | Streamlit default (~1rem) |
| Section dividers | `st.divider()` — renders as `#21262d` horizontal rule |

### Chart Margins (Plotly `margin` dict)

| Side | Value |
|---|---|
| Top (`t`) | 60px |
| Bottom (`b`) | 40px |
| Left (`l`) | 40px |
| Right (`r`) | 40px |

### Chart Heights

| Chart | Height |
|---|---|
| `plot_allocation` | 520px |
| `plot_gainloss_dollar` | 480px (scales with position count in Phase 1.x) |
| `plot_gainloss_pct` | 480px |
| `plot_cost_vs_value` | 480px |
| `plot_return_vs_weight` | 520px |

### Metric Card Grid

Six columns, equal width (`st.columns(6)`). Cards have:
- Background: `SURFACE` (`#161b22`)
- Border: 1px solid `BORDER` (`#21262d`)
- Border-radius: 8px
- Padding: 16px

### Expander (raw data table)

- `expanded=False` by default
- Full-width table inside (`use_container_width=True`)
- No additional padding beyond Streamlit defaults

---

## 5. Component Specifications

### File Uploader

| Property | Value |
|---|---|
| Accepted types | `["csv"]` |
| Label | "Upload M1 Holdings CSV" |
| Help text | One sentence explaining local-only privacy |
| Empty state | `st.info()` with upward arrow emoji and instruction |

### Metric Cards (`st.metric`)

| State | Delta color |
|---|---|
| Positive delta | `GREEN` (`#3fb950`) automatically via Streamlit |
| Negative delta | `RED` (`#f85149`) automatically via Streamlit |

Format rules:
- Dollar values: `${:,.2f}` with `+` sign for gain/loss
- Percentage values: `{:+.2f}%`
- Integer counts: no formatting (positions, winners, losers)
- Ticker symbols: uppercase, no formatting

### Tabs

Six tabs in Phase 1 (five charts + Phase 2 will add more):

| Emoji + Label | Chart |
|---|---|
| 🥧  Allocation | `plot_allocation` |
| 💵  Gain / Loss ($) | `plot_gainloss_dollar` |
| 📊  Gain / Loss (%) | `plot_gainloss_pct` |
| ⚖️  Cost vs Value | `plot_cost_vs_value` |
| 🎯  Return vs Weight | `plot_return_vs_weight` |

Selected tab: `ACCENT` underline (`#58a6ff`). Unselected: `MUTED` text (`#8b949e`).

### Data Table (`st.dataframe`)

Column format map:

| Column | Format |
|---|---|
| `quantity` | `{:.5f}` |
| `avg_price` | `${:,.2f}` |
| `cost_basis` | `${:,.2f}` |
| `unrealized_gain_dollar` | `${:+,.2f}` |
| `unrealized_gain_pct` | `{:+.2f}%` |
| `current_value` | `${:,.2f}` |
| `portfolio_weight_pct` | `{:.1f}%` |

---

## 6. Chart Design System

### BASE_LAYOUT (applied to all charts)

```python
BASE_LAYOUT = dict(
    paper_bgcolor = "#0d1117",
    plot_bgcolor  = "#0d1117",
    font          = dict(family="monospace", color="#e6edf3", size=12),
    xaxis         = dict(gridcolor="#21262d", zerolinecolor="#21262d"),
    yaxis         = dict(gridcolor="#21262d", zerolinecolor="#21262d"),
    margin        = dict(t=60, b=40, l=40, r=40),
    hoverlabel    = dict(bgcolor="#161b22", font_color="#e6edf3", font_family="monospace"),
)
```

### Chart Titles

- Font size: 14px
- Color: `TEXT` (`#e6edf3`)
- Position: top-left (Plotly default)
- Format: `"Chart Name — Subtitle Detail"` (em dash separator)

### Hover Tooltips

- Background: `SURFACE` (`#161b22`)
- Text color: `TEXT` (`#e6edf3`)
- Font: monospace, 12px
- Format: bold symbol on line 1, labeled metrics below, `<extra></extra>` to suppress
  Plotly's default trace name box

### Bar Charts (horizontal — charts 2 and 3)

- Orientation: horizontal (`orientation="h"`)
- Color: conditional — `GREEN` if value ≥ 0, `RED` if value < 0
- Zero reference line: `add_vline(x=0, line_color=MUTED, line_width=1, line_dash="dot")`
- Sort order: ascending by the primary metric (smallest at top, largest at bottom)
- No bar border (Plotly default)

### Bar Charts (grouped vertical — chart 4)

- Mode: `barmode="group"`
- Cost Basis series: `MUTED` color (`#8b949e`), `opacity=0.8`
- Current Value series: `ACCENT` color (`#58a6ff`)
- Legend: horizontal, positioned at top-left above chart

### Donut Chart (chart 1)

- Hole size: 0.58 (generous center for total annotation)
- Text: `"label+percent"`, position `"inside"`
- Line between slices: 2px `BG` color (creates visual separation)
- Center annotation: bold total value on line 1, "Total Value" subtitle in `MUTED` at 11px

### Scatter/Bubble Chart (chart 5)

- Mode: `"markers+text"`
- Marker size: scaled proportionally to `current_value` — range 10px to 70px
  Formula: `current_value / max_value * 60 + 10`
- Marker opacity: 0.75
- Marker border: 1.5px `BG` color (prevents overlap bleed)
- Text labels: `TOP CENTER`, `TEXT` color, 11px
- Zero reference line: `add_hline(y=0, ...)`

---

## 7. Interaction Design

### Hover States
All Plotly charts support hover natively. Hover tooltips follow the spec in §6.

Streamlit hover states for metric cards are handled via CSS:
```css
[data-testid="stMetric"]:hover {
    background-color: #1c2128;
    transition: background-color 0.15s ease;
}
```
*(Add in Phase 1.x — not in initial scaffold)*

### Zoom and Pan
Plotly provides zoom/pan on all charts by default via the toolbar.
No custom zoom behavior needed. Double-click resets to full extent.

### Click Behavior
Phase 1: no click actions on charts. Charts are read-only visualizations.
Phase 2+: clicking a position in the donut or scatter may filter the snapshot diff view.

### Responsive Behavior
All charts use `use_container_width=True` in `st.plotly_chart()`. They reflow to fit
any viewport width. Minimum usable width is approximately 800px; below this, horizontal
bar labels may truncate. No mobile optimization is planned for Phase 1.

---

## 8. Error and Empty States

### Upload Error
- Container: `st.error()` (Streamlit native red alert box)
- Content: bold "Could not parse your CSV." on line 1, full `ValueError` message below
- No custom styling needed

### No File Uploaded
- Container: `st.info()` (Streamlit native blue info box)
- Content: "⬆️  Drop your M1 holdings CSV above to get started."
- Followed by `st.stop()` — nothing else renders

### Unexpected Exception
- Container: `st.error()`
- Content: "**Unexpected error loading file:** {exception}"

---

## 9. CSS Injection Reference

Applied in `app.py` via `st.markdown(..., unsafe_allow_html=True)`.

```css
/* Page background */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #e6edf3;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 16px;
}
[data-testid="stMetricLabel"]  { color: #8b949e; font-size: 12px; }
[data-testid="stMetricValue"]  { color: #e6edf3; }
[data-testid="stMetricDelta"]  { font-size: 13px; }

/* Tabs */
.stTabs [data-baseweb="tab"]          { color: #8b949e; }
.stTabs [aria-selected="true"]        { color: #58a6ff; border-bottom-color: #58a6ff; }

/* Divider */
hr { border-color: #21262d; }
```

---

## 10. Versioning This Document

This document covers Phase 1. Design additions for Phase 2+ (date pickers, snapshot
selectors, timeline charts) will be appended as addenda. No retroactive changes to
Phase 1 tokens without a documented rationale.
