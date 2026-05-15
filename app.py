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
import streamlit as st
from core.loader import (
    load_m1_csv,
    portfolio_summary,
    parse_snapshot_date,
    load_snapshots,
    snapshot_diff,
)
from charts.chart_engine import (
    plot_allocation,
    plot_gainloss_dollar,
    plot_gainloss_pct,
    plot_cost_vs_value,
    plot_return_vs_weight,
    plot_portfolio_timeline,
    plot_position_delta,
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
    }
    [data-testid="stMetricLabel"] { color: #8b949e; font-size: 12px; }
    [data-testid="stMetricValue"] { color: #e6edf3; }
    [data-testid="stMetricDelta"] { font-size: 13px; }
    .stTabs [data-baseweb="tab"] { color: #8b949e; }
    .stTabs [aria-selected="true"] { color: #58a6ff; border-bottom-color: #58a6ff; }
    hr { border-color: #21262d; }
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


def _render_metrics(summary: dict) -> None:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Value",       f"${summary['total_value']:,.2f}")
    c2.metric("Total Gain / Loss", f"${summary['total_gain']:+,.2f}", f"{summary['total_return_pct']:+.2f}%")
    c3.metric("Positions",         summary["positions"])
    c4.metric("Winners 🟢",        summary["winners"])
    c5.metric("Losers 🔴",         summary["losers"])
    c6.metric("Best Performer",    summary["best_performer"])


def _render_raw_table(df) -> None:
    with st.expander("View raw holdings data", expanded=False):
        st.dataframe(
            df.style.format({
                "quantity":               "{:.5f}",
                "avg_price":              "${:,.2f}",
                "cost_basis":             "${:,.2f}",
                "unrealized_gain_dollar": "${:+,.2f}",
                "unrealized_gain_pct":    "{:+.2f}%",
                "current_value":          "${:,.2f}",
                "portfolio_weight_pct":   "{:.1f}%",
            }),
            use_container_width=True,
        )


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
    _render_raw_table(df)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🥧  Allocation",
        "💵  Gain / Loss ($)",
        "📊  Gain / Loss (%)",
        "⚖️  Cost vs Value",
        "🎯  Return vs Weight",
    ])

    with tab1: st.plotly_chart(plot_allocation(df),       use_container_width=True)
    with tab2: st.plotly_chart(plot_gainloss_dollar(df),  use_container_width=True)
    with tab3: st.plotly_chart(plot_gainloss_pct(df),     use_container_width=True)
    with tab4: st.plotly_chart(plot_cost_vs_value(df),    use_container_width=True)
    with tab5: st.plotly_chart(plot_return_vs_weight(df), use_container_width=True)


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

    _render_metrics(portfolio_summary(latest_df))
    st.divider()
    _render_raw_table(latest_df)

    all_symbols = sorted({sym for df in snapshots.values() for sym in df["symbol"]})

    (tab_timeline, tab_trend, tab_diff,
     tab1, tab2, tab3, tab4, tab5) = st.tabs([
        "📅  Timeline",
        "📈  Position Trend",
        "🔄  Snapshot Diff",
        "🥧  Allocation",
        "💵  Gain / Loss ($)",
        "📊  Gain / Loss (%)",
        "⚖️  Cost vs Value",
        "🎯  Return vs Weight",
    ])

    with tab_timeline:
        st.plotly_chart(plot_portfolio_timeline(snapshots), use_container_width=True)

    with tab_trend:
        symbol = st.selectbox("Select position", all_symbols, key="trend_symbol")
        st.plotly_chart(plot_position_delta(snapshots, symbol), use_container_width=True)

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
                use_container_width=True,
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
                use_container_width=True,
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
                use_container_width=True,
            )

    with tab1: st.plotly_chart(plot_allocation(latest_df),       use_container_width=True)
    with tab2: st.plotly_chart(plot_gainloss_dollar(latest_df),  use_container_width=True)
    with tab3: st.plotly_chart(plot_gainloss_pct(latest_df),     use_container_width=True)
    with tab4: st.plotly_chart(plot_cost_vs_value(latest_df),    use_container_width=True)
    with tab5: st.plotly_chart(plot_return_vs_weight(latest_df), use_container_width=True)


st.divider()
st.caption(
    "m1-portfolio-kit · Open source · "
    "Data never leaves your machine · "
    "[GitHub](https://github.com/JaydotMurf/m1-portfolio-kit)"
)
