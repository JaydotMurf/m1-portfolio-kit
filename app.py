"""
app.py
------
M1 Portfolio Kit — Streamlit entry point.

Phase 1 (single CSV):  upload one M1 holdings export for five interactive charts.
Phase 2 (multi-CSV):   upload multiple exports to track your portfolio over time.

Run locally:
    streamlit run app.py
"""

import datetime
import pandas as pd
import streamlit as st
from core.loader import (
    load_m1_csv,
    portfolio_summary,
    parse_snapshot_date,
    load_snapshots,
    snapshot_diff,
    compute_snapshot_change,
    fetch_benchmark,
)
from charts.chart_engine import (
    plot_allocation,
    plot_gainloss_dollar,
    plot_gainloss_pct,
    plot_cost_vs_value,
    plot_return_vs_weight,
    plot_portfolio_radar,
    plot_portfolio_timeline,
    plot_position_delta,
    plot_heatmap,
)
from charts.detail_panel import (
    plot_position_value,
    plot_position_cost,
    plot_position_quantity,
)

st.set_page_config(
    page_title="M1 Portfolio Kit",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
        color: #e6edf3;
    }
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 16px;
        overflow: visible;
    }
    [data-testid="stMetricLabel"] { color: #8b949e; font-size: 12px; }
    [data-testid="stMetricValue"] { color: #e6edf3; white-space: nowrap; overflow: visible; }
    [data-testid="stMetricDelta"] { font-size: 13px; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; }
    .stTabs [aria-selected="true"] { color: #58a6ff; border-bottom-color: #58a6ff; }
    hr { border-color: #21262d; }

    /* ── Responsive KPI strip (scoped to new dashboard area) ── */
    .kpi-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 4px;
    }
    .kpi-card {
        flex: 1 1 140px;
        background-color: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 16px;
        font-family: monospace;
        min-width: 120px;
        box-sizing: border-box;
    }
    .kpi-label { color: #8b949e; font-size: 12px; margin-bottom: 4px; }
    .kpi-value { color: #e6edf3; font-size: 20px; font-weight: bold; white-space: nowrap; }
    .kpi-delta { font-size: 13px; margin-top: 4px; }
    .kpi-pos   { color: #3fb950; }
    .kpi-neg   { color: #f85149; }
    .kpi-neu   { color: #8b949e; }

    /* 3-per-row at ≤ 900 px  →  3×2 */
    @media (max-width: 900px) {
        .kpi-card { flex: 1 1 calc(33.33% - 12px); }
    }
    /* 2-per-row at ≤ 600 px  →  2×3 */
    @media (max-width: 600px) {
        .kpi-card { flex: 1 1 calc(50% - 12px); }
    }
    /* 1-per-row at ≤ 480 px  →  1×5 */
    @media (max-width: 480px) {
        .kpi-card { flex: 1 1 100%; }
    }

    /* Prevent horizontal overflow on the heatmap container at narrow viewports */
    [data-testid="stPlotlyChart"] { overflow-x: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("📈 M1 Portfolio Kit")
st.caption(
    "Visualize your M1 Finance holdings. "
    "Export your CSV from M1: **Portfolio → Holdings → ... → Export CSV**"
)

st.divider()

uploaded_files = st.file_uploader(
    label="Upload M1 Holdings CSV",
    type=["csv"],
    accept_multiple_files=True,
    help=(
        "Upload one CSV for single-snapshot analysis. "
        "Upload multiple CSVs to track your portfolio over time."
    ),
)

if not uploaded_files:
    st.info("⬆️  Drop your M1 holdings CSV above to get started.")
    st.stop()


def _render_metrics(summary: dict, change: dict | None = None) -> None:
    def _delta(val: float, text: str) -> str:
        cls = "kpi-pos" if val > 0 else ("kpi-neg" if val < 0 else "kpi-neu")
        return f"<div class='kpi-delta {cls}'>{text}</div>"

    def _card(label: str, value: str, delta: str = "") -> str:
        return (
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value}</div>"
            f"{delta}"
            f"</div>"
        )

    if change is not None:
        html = "".join([
            _card("Total Value",     f"${summary['total_value']:,.2f}"),
            _card("Gain / Loss",     f"${summary['total_gain']:+,.2f}",
                  _delta(summary['total_return_pct'], f"{summary['total_return_pct']:+.2f}%")),
            _card("Snapshot Change", f"${change['delta_dollar']:+,.2f}",
                  _delta(change['delta_pct'], f"{change['delta_pct']:+.2f}%")),
            _card("Positions",       str(summary["positions"])),
            _card("Best Performer",  summary["best_performer"]),
        ])
    else:
        html = "".join([
            _card("Total Value",     f"${summary['total_value']:,.2f}"),
            _card("Gain / Loss",     f"${summary['total_gain']:+,.2f}",
                  _delta(summary['total_return_pct'], f"{summary['total_return_pct']:+.2f}%")),
            _card("Positions",       str(summary["positions"])),
            _card("Best Performer",  summary["best_performer"]),
            _card("Worst Performer", summary["worst_performer"]),
        ])

    st.markdown(f"<div class='kpi-strip'>{html}</div>", unsafe_allow_html=True)


def _render_raw_table(df) -> None:
    # Rename columns to professional title case
    display_df = df.rename(columns={
        "symbol": "Symbol",
        "name": "Name",
        "quantity": "Quantity",
        "avg_price": "Avg Price",
        "cost_basis": "Cost Basis",
        "unrealized_gain_dollar": "Unrealized Gain ($)",
        "unrealized_gain_pct": "Unrealized Gain (%)",
        "current_value": "Current Value",
        "portfolio_weight_pct": "Portfolio Weight (%)",
    })

    # Custom formatters with directional arrows
    def format_gain_loss_dollar(val):
        if pd.isna(val):
            return ""
        arrow = "▲" if val > 0 else "▼"
        return f"{arrow} ${val:+,.2f}"

    def format_gain_loss_pct(val):
        if pd.isna(val):
            return ""
        arrow = "▲" if val > 0 else "▼"
        return f"{arrow} {val:+.2f}%"

    # Color styling for gain/loss columns
    def color_gain_loss(val):
        if pd.isna(val):
            return ""
        if val > 0:
            return "background-color: #3fb950; color: #0d1117; font-weight: bold;"
        elif val < 0:
            return "background-color: #f85149; color: #0d1117; font-weight: bold;"
        return ""

    with st.expander("View raw holdings data", expanded=False):
        st.dataframe(
            display_df.style
            .map(color_gain_loss, subset=["Unrealized Gain ($)", "Unrealized Gain (%)"])
            .format({
                "Quantity":              "{:.5f}",
                "Avg Price":             "${:,.2f}",
                "Cost Basis":            "${:,.2f}",
                "Unrealized Gain ($)":   format_gain_loss_dollar,
                "Unrealized Gain (%)":   format_gain_loss_pct,
                "Current Value":         "${:,.2f}",
                "Portfolio Weight (%)":  "{:.1f}%",
            }),
            width='stretch',
        )


def _render_position_cards(df) -> None:
    """
    Render a compact card grid — 5 cards per row, sorted by current_value descending.
    Shows: symbol, current value, portfolio weight, return %, gain/loss $.
    Gain/loss and return are color-coded green/red using design tokens.
    """
    sorted_df = df.sort_values("current_value", ascending=False).reset_index(drop=True)

    def _card_html(row) -> str:
        gain_color   = "#3fb950" if row["unrealized_gain_dollar"] >= 0 else "#f85149"
        return_color = "#3fb950" if row["unrealized_gain_pct"]    >= 0 else "#f85149"
        return (
            "<div style='"
            "background-color:#161b22;"
            "border:1px solid #21262d;"
            "border-radius:8px;"
            "padding:12px 8px;"
            "text-align:center;"
            "font-family:monospace;"
            "'>"
            f"<div style='font-size:16px;font-weight:bold;color:#e6edf3;'>{row['symbol']}</div>"
            f"<div style='font-size:11px;color:#8b949e;margin:3px 0;'>${row['current_value']:,.0f}</div>"
            f"<div style='font-size:11px;color:#8b949e;'>{row['portfolio_weight_pct']:.1f}%</div>"
            f"<div style='font-size:13px;color:{return_color};font-weight:bold;margin-top:5px;'>{row['unrealized_gain_pct']:+.1f}%</div>"
            f"<div style='font-size:11px;color:{gain_color};'>${row['unrealized_gain_dollar']:+,.0f}</div>"
            "</div>"
        )

    chunk_size = 5
    for start in range(0, len(sorted_df), chunk_size):
        chunk = sorted_df.iloc[start : start + chunk_size]
        cols  = st.columns(len(chunk))
        for col, (_, row) in zip(cols, chunk.iterrows()):
            col.markdown(_card_html(row), unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)


def _render_position_detail(row: pd.Series, snapshots: dict | None = None) -> None:
    """Detail panel for a clicked heatmap tile."""
    st.divider()
    st.subheader(f"{row['symbol']} — {row['name']}")
    st.caption(f"Sector: {row['sector']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Value",    f"${row['current_value']:,.2f}")
    c2.metric("Cost Basis",       f"${row['cost_basis']:,.2f}")
    c3.metric("Return",           f"{row['unrealized_gain_pct']:+.2f}%",
                                  f"${row['unrealized_gain_dollar']:+,.2f}")
    c4.metric("Portfolio Weight", f"{row['portfolio_weight_pct']:.1f}%")

    if snapshots is not None:
        col_v, col_c, col_q = st.columns(3)
        symbol = row["symbol"]
        with col_v:
            st.plotly_chart(plot_position_value(snapshots, symbol),    width='stretch')
        with col_c:
            st.plotly_chart(plot_position_cost(snapshots, symbol),     width='stretch')
        with col_q:
            st.plotly_chart(plot_position_quantity(snapshots, symbol), width='stretch')


def _heatmap_selection(event, symbol_set: set) -> str | None:
    """Return the clicked symbol if a position tile was selected, else None."""
    try:
        points = event.selection.points
        if points:
            label = points[0].get("label", "")
            if label in symbol_set:
                return label
    except (AttributeError, IndexError, TypeError):
        pass
    return None


# ── Phase 1: single-snapshot ──────────────────────────────────────────────────
if len(uploaded_files) == 1:
    try:
        df = load_m1_csv(uploaded_files[0])
    except ValueError as e:
        st.error(f"**Could not parse your CSV.**\n\n{e}")
        st.stop()
    except Exception as e:
        st.error(f"**Unexpected error loading file:** {e}")
        st.stop()

    summary = portfolio_summary(df)
    _render_metrics(summary)
    st.divider()

    (tab_overview,
     tab1, tab2, tab3, tab4, tab5, tab6) = st.tabs([
        "🗺️  Overview",
        "🥧  Allocation",
        "💵  Gain / Loss ($)",
        "📊  Gain / Loss (%)",
        "⚖️  Cost vs Value",
        "🎯  Return vs Weight",
        "🕸️  Radar",
    ])

    with tab_overview:
        event = st.plotly_chart(
            plot_heatmap(df), width='stretch',
            on_select="rerun", selection_mode="points", key="heatmap_single",
        )
        selected = _heatmap_selection(event, set(df["symbol"]))
        if selected:
            row = df[df["symbol"] == selected].iloc[0]
            _render_position_detail(row)
        _render_raw_table(df)
    with tab1: st.plotly_chart(plot_allocation(df),        width='stretch')
    with tab2: st.plotly_chart(plot_gainloss_dollar(df),   width='stretch')
    with tab3: st.plotly_chart(plot_gainloss_pct(df),      width='stretch')
    with tab4: st.plotly_chart(plot_cost_vs_value(df),     width='stretch')
    with tab5: st.plotly_chart(plot_return_vs_weight(df),  width='stretch')
    with tab6: st.plotly_chart(plot_portfolio_radar(df),   width='stretch')


# ── Phase 2: multi-snapshot ───────────────────────────────────────────────────
else:
    st.caption("Confirm the snapshot date for each uploaded file:")
    date_map = {}
    for f in uploaded_files:
        parsed  = parse_snapshot_date(f.name)
        default = datetime.date.fromisoformat(parsed) if parsed else datetime.date.today()
        chosen  = st.date_input(f.name, value=default, key=f"snapdate_{f.name}")
        date_map[f.name] = str(chosen)

    st.divider()

    try:
        snapshots = load_snapshots(uploaded_files, date_map)
    except ValueError as e:
        st.error(f"**Snapshot date conflict.**\n\n{e}")
        st.stop()
    except Exception as e:
        st.error(f"**Unexpected error:** {e}")
        st.stop()

    latest_df = list(snapshots.values())[-1]
    dates     = sorted(snapshots.keys())
    change    = compute_snapshot_change(snapshots)

    _render_metrics(portfolio_summary(latest_df), change)
    st.divider()

    all_symbols = sorted({sym for df in snapshots.values() for sym in df["symbol"]})

    (tab_overview, tab_timeline, tab_trend, tab_diff,
     tab1, tab2, tab3, tab4, tab5) = st.tabs([
        "🗺️  Overview",
        "📅  Timeline",
        "📈  Position Trend",
        "🔄  Snapshot Diff",
        "🥧  Allocation",
        "💵  Gain / Loss ($)",
        "📊  Gain / Loss (%)",
        "⚖️  Cost vs Value",
        "🎯  Return vs Weight",
    ])

    with tab_overview:
        event = st.plotly_chart(
            plot_heatmap(latest_df), width='stretch',
            on_select="rerun", selection_mode="points", key="heatmap_multi",
        )
        selected = _heatmap_selection(event, set(latest_df["symbol"]))
        if selected:
            row = latest_df[latest_df["symbol"] == selected].iloc[0]
            _render_position_detail(row, snapshots)
        _render_raw_table(latest_df)

    with tab_timeline:
        show_bench = st.checkbox(
            "Show benchmark comparison — requires internet connection",
            key="show_benchmarks",
        )
        benchmarks = None
        if show_bench:
            selected = st.multiselect(
                "Select benchmarks", ["SPY", "QQQ"], default=["SPY"], key="bench_tickers"
            )
            if selected:
                benchmarks = fetch_benchmark(selected, start=dates[0], end=dates[-1])
                if benchmarks is None:
                    st.warning(
                        "Could not fetch benchmark data. Check your internet connection "
                        "or install the optional dependency: `pip install yfinance`"
                    )
        st.plotly_chart(
            plot_portfolio_timeline(snapshots, benchmarks), width='stretch'
        )

    with tab_trend:
        symbol = st.selectbox("Select position", all_symbols, key="trend_symbol")
        st.plotly_chart(plot_position_delta(snapshots, symbol), width='stretch')

    with tab_diff:
        diff_df = snapshot_diff(snapshots)
        st.caption(f"Comparing **{dates[0]}** → **{dates[-1]}**")

        held   = diff_df[diff_df["status"] == "held"]
        new    = diff_df[diff_df["status"] == "new"]
        closed = diff_df[diff_df["status"] == "closed"]

        if not held.empty:
            st.subheader("Held positions")
            st.dataframe(
                held[[
                    "symbol", "name",
                    "current_value_old", "current_value_new", "value_change",
                    "unrealized_gain_pct_old", "unrealized_gain_pct_new", "return_change_pp",
                    "portfolio_weight_pct_old", "portfolio_weight_pct_new", "weight_change_pp",
                ]].style.format({
                    "current_value_old":        "${:,.2f}",
                    "current_value_new":        "${:,.2f}",
                    "value_change":             "${:+,.2f}",
                    "unrealized_gain_pct_old":  "{:+.2f}%",
                    "unrealized_gain_pct_new":  "{:+.2f}%",
                    "return_change_pp":         "{:+.2f}pp",
                    "portfolio_weight_pct_old": "{:.1f}%",
                    "portfolio_weight_pct_new": "{:.1f}%",
                    "weight_change_pp":         "{:+.2f}pp",
                }),
                width='stretch',
            )

        if not new.empty:
            st.subheader("New positions")
            st.dataframe(
                new[["symbol", "name",
                     "current_value_new", "unrealized_gain_pct_new", "portfolio_weight_pct_new",
                ]].style.format({
                    "current_value_new":        "${:,.2f}",
                    "unrealized_gain_pct_new":  "{:+.2f}%",
                    "portfolio_weight_pct_new": "{:.1f}%",
                }),
                width='stretch',
            )

        if not closed.empty:
            st.subheader("Closed positions")
            st.dataframe(
                closed[["symbol", "name",
                        "current_value_old", "unrealized_gain_pct_old", "portfolio_weight_pct_old",
                ]].style.format({
                    "current_value_old":        "${:,.2f}",
                    "unrealized_gain_pct_old":  "{:+.2f}%",
                    "portfolio_weight_pct_old": "{:.1f}%",
                }),
                width='stretch',
            )

    with tab1: st.plotly_chart(plot_allocation(latest_df),       width='stretch')
    with tab2: st.plotly_chart(plot_gainloss_dollar(latest_df),  width='stretch')
    with tab3: st.plotly_chart(plot_gainloss_pct(latest_df),     width='stretch')
    with tab4: st.plotly_chart(plot_cost_vs_value(latest_df),    width='stretch')
    with tab5: st.plotly_chart(plot_return_vs_weight(latest_df), width='stretch')


st.divider()
st.caption(
    "m1-portfolio-kit · Open source · "
    "Data never leaves your machine · "
    "[GitHub](https://github.com/JaydotMurf/m1-portfolio-kit)"
)
