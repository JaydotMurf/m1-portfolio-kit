"""
app.py
------
M1 Portfolio Kit — Streamlit entry point.

Run locally:
    streamlit run app.py

Upload your M1 Finance holdings CSV to get started.
Export path inside M1: Portfolio → Holdings → ... → Export CSV
"""

import streamlit as st
from core.loader import load_m1_csv, portfolio_summary
from charts.chart_engine import (
    plot_allocation,
    plot_gainloss_dollar,
    plot_gainloss_pct,
    plot_cost_vs_value,
    plot_return_vs_weight,
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

uploaded_file = st.file_uploader(
    label="Upload M1 Holdings CSV",
    type=["csv"],
    help="Use M1's built-in export. No account credentials are sent anywhere — "
         "this tool runs entirely on your local machine.",
)

if uploaded_file is None:
    st.info("⬆️  Drop your M1 holdings CSV above to get started.")
    st.stop()

try:
    df = load_m1_csv(uploaded_file)
except ValueError as e:
    st.error(f"**Could not parse your CSV.**\n\n{e}")
    st.stop()
except Exception as e:
    st.error(f"**Unexpected error loading file:** {e}")
    st.stop()

summary = portfolio_summary(df)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Value", f"${summary['total_value']:,.2f}")
c2.metric("Total Gain / Loss", f"${summary['total_gain']:+,.2f}", f"{summary['total_return_pct']:+.2f}%")
c3.metric("Positions", summary["positions"])
c4.metric("Winners 🟢", summary["winners"])
c5.metric("Losers 🔴", summary["losers"])
c6.metric("Best Performer", summary["best_performer"])

st.divider()

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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🥧  Allocation",
    "💵  Gain / Loss ($)",
    "📊  Gain / Loss (%)",
    "⚖️  Cost vs Value",
    "🎯  Return vs Weight",
])

with tab1:
    st.plotly_chart(plot_allocation(df), use_container_width=True)
with tab2:
    st.plotly_chart(plot_gainloss_dollar(df), use_container_width=True)
with tab3:
    st.plotly_chart(plot_gainloss_pct(df), use_container_width=True)
with tab4:
    st.plotly_chart(plot_cost_vs_value(df), use_container_width=True)
with tab5:
    st.plotly_chart(plot_return_vs_weight(df), use_container_width=True)

st.divider()
st.caption(
    "m1-portfolio-kit · Open source · "
    "Data never leaves your machine · "
    "[GitHub](https://github.com/JaydotMurf/m1-portfolio-kit)"
)
