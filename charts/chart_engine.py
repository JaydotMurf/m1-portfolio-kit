"""
charts/chart_engine.py
----------------------
Five interactive Plotly charts built from a single M1 holdings snapshot.
All functions accept a normalized DataFrame from core/loader.py and return
a plotly.graph_objects.Figure ready for st.plotly_chart().

Charts
------
1. plot_allocation       — Portfolio weight by current value (donut)
2. plot_gainloss_dollar  — Unrealized gain/loss per position ($)
3. plot_gainloss_pct     — Unrealized gain/loss per position (%)
4. plot_cost_vs_value    — Cost basis vs current value side-by-side
5. plot_return_vs_weight — Return % vs portfolio weight scatter
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Design constants ─────────────────────────────────────────────────────────
BG        = "#0d1117"
PAPER     = "#0d1117"
GRID      = "#21262d"
TEXT      = "#e6edf3"
MUTED     = "#8b949e"
GREEN     = "#3fb950"
RED       = "#f85149"
ACCENT    = "#58a6ff"
FONT      = "monospace"

BASE_LAYOUT = dict(
    paper_bgcolor = PAPER,
    plot_bgcolor  = BG,
    font          = dict(family=FONT, color=TEXT, size=12),
    xaxis         = dict(gridcolor=GRID, zerolinecolor=GRID),
    yaxis         = dict(gridcolor=GRID, zerolinecolor=GRID),
    margin        = dict(t=60, b=40, l=40, r=40),
    hoverlabel    = dict(bgcolor="#161b22", font_color=TEXT, font_family=FONT),
)

PALETTE = px.colors.qualitative.T10


def _apply_base(fig: go.Figure, title: str, height: int = 480) -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=14, color=TEXT)),
                      height=height, **BASE_LAYOUT)
    return fig


# ── Chart 1: Portfolio Allocation ────────────────────────────────────────────
def plot_allocation(df: pd.DataFrame) -> go.Figure:
    sorted_df = df.sort_values("current_value", ascending=False)

    fig = go.Figure(go.Pie(
        labels       = sorted_df["symbol"],
        values       = sorted_df["current_value"],
        hole         = 0.58,
        marker       = dict(colors=PALETTE, line=dict(color=BG, width=2)),
        textinfo     = "label+percent",
        textposition = "inside",
        hovertemplate = (
            "<b>%{label}</b><br>"
            "Value: $%{value:,.2f}<br>"
            "Weight: %{percent}<extra></extra>"
        ),
    ))

    total = df["current_value"].sum()
    fig.add_annotation(
        text=f"<b>${total:,.0f}</b><br><span style='font-size:11px;color:{MUTED}'>Total Value</span>",
        x=0.5, y=0.5, showarrow=False, align="center",
        font=dict(size=16, color=TEXT),
    )

    return _apply_base(fig, "Portfolio Allocation — Current Value", height=520)


# ── Chart 2: Unrealized Gain / Loss ($) ──────────────────────────────────────
def plot_gainloss_dollar(df: pd.DataFrame) -> go.Figure:
    sorted_df = df.sort_values("unrealized_gain_dollar")
    colors = [GREEN if v >= 0 else RED for v in sorted_df["unrealized_gain_dollar"]]

    fig = go.Figure(go.Bar(
        x           = sorted_df["unrealized_gain_dollar"],
        y           = sorted_df["symbol"],
        orientation = "h",
        marker_color = colors,
        customdata  = sorted_df[["name", "unrealized_gain_pct"]].values,
        hovertemplate = (
            "<b>%{y}</b> — %{customdata[0]}<br>"
            "Gain/Loss: $%{x:+,.2f}<br>"
            "Return: %{customdata[1]:+.1f}%<extra></extra>"
        ),
    ))

    fig.add_vline(x=0, line_color=MUTED, line_width=1, line_dash="dot")
    fig.update_layout(xaxis_title="Unrealized Gain / Loss ($)", yaxis_title=None)

    return _apply_base(fig, "Unrealized Gain / Loss by Position ($)")


# ── Chart 3: Unrealized Gain / Loss (%) ──────────────────────────────────────
def plot_gainloss_pct(df: pd.DataFrame) -> go.Figure:
    sorted_df = df.sort_values("unrealized_gain_pct")
    colors = [GREEN if v >= 0 else RED for v in sorted_df["unrealized_gain_pct"]]

    fig = go.Figure(go.Bar(
        x           = sorted_df["unrealized_gain_pct"],
        y           = sorted_df["symbol"],
        orientation = "h",
        marker_color = colors,
        customdata  = sorted_df[["name", "unrealized_gain_dollar"]].values,
        hovertemplate = (
            "<b>%{y}</b> — %{customdata[0]}<br>"
            "Return: %{x:+.2f}%<br>"
            "Gain/Loss: $%{customdata[1]:+,.2f}<extra></extra>"
        ),
    ))

    fig.add_vline(x=0, line_color=MUTED, line_width=1, line_dash="dot")
    fig.update_layout(xaxis_title="Unrealized Return (%)", yaxis_title=None)

    return _apply_base(fig, "Unrealized Return by Position (%)")


# ── Chart 4: Cost Basis vs Current Value ─────────────────────────────────────
def plot_cost_vs_value(df: pd.DataFrame) -> go.Figure:
    sorted_df = df.sort_values("current_value", ascending=False)

    fig = go.Figure([
        go.Bar(
            name        = "Cost Basis",
            x           = sorted_df["symbol"],
            y           = sorted_df["cost_basis"],
            marker_color = MUTED,
            opacity     = 0.8,
            hovertemplate = "<b>%{x}</b><br>Cost Basis: $%{y:,.2f}<extra></extra>",
        ),
        go.Bar(
            name        = "Current Value",
            x           = sorted_df["symbol"],
            y           = sorted_df["current_value"],
            marker_color = ACCENT,
            hovertemplate = "<b>%{x}</b><br>Current Value: $%{y:,.2f}<extra></extra>",
        ),
    ])

    fig.update_layout(
        barmode     = "group",
        xaxis_title = None,
        yaxis_title = "Value ($)",
        legend      = dict(
            orientation = "h", x=0, y=1.08,
            font=dict(color=TEXT),
            bgcolor=BG, bordercolor=GRID,
        ),
    )

    return _apply_base(fig, "Cost Basis vs Current Value by Position")


# ── Chart 5: Return % vs Portfolio Weight ─────────────────────────────────────
def plot_return_vs_weight(df: pd.DataFrame) -> go.Figure:
    colors = [GREEN if v >= 0 else RED for v in df["unrealized_gain_pct"]]

    fig = go.Figure(go.Scatter(
        x           = df["portfolio_weight_pct"],
        y           = df["unrealized_gain_pct"],
        mode        = "markers+text",
        marker      = dict(
            size        = df["current_value"] / df["current_value"].max() * 60 + 10,
            color       = colors,
            opacity     = 0.75,
            line        = dict(color=BG, width=1.5),
        ),
        text        = df["symbol"],
        textposition = "top center",
        textfont    = dict(color=TEXT, size=11),
        customdata  = df[["name", "current_value", "unrealized_gain_dollar"]].values,
        hovertemplate = (
            "<b>%{text}</b> — %{customdata[0]}<br>"
            "Weight: %{x:.1f}%<br>"
            "Return: %{y:+.1f}%<br>"
            "Value: $%{customdata[1]:,.2f}<br>"
            "Gain/Loss: $%{customdata[2]:+,.2f}<extra></extra>"
        ),
    ))

    fig.add_hline(y=0, line_color=MUTED, line_width=1, line_dash="dot")
    fig.update_layout(
        xaxis_title = "Portfolio Weight (%)",
        yaxis_title = "Unrealized Return (%)",
    )

    return _apply_base(fig, "Return % vs Portfolio Weight — Bubble = Position Size", height=520)


# ── Phase 2 charts ────────────────────────────────────────────────────────────

def plot_portfolio_timeline(snapshots: dict) -> go.Figure:
    """Line chart of total portfolio value across snapshots."""
    dates  = list(snapshots.keys())
    values = [df["current_value"].sum() for df in snapshots.values()]

    fig = go.Figure(go.Scatter(
        x             = dates,
        y             = values,
        mode          = "lines+markers",
        line          = dict(color=ACCENT, width=2),
        marker        = dict(size=8, color=ACCENT),
        hovertemplate = "<b>%{x}</b><br>Portfolio Value: $%{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(xaxis_title=None, yaxis_title="Total Value ($)")
    return _apply_base(fig, "Portfolio Value Over Time")


def plot_position_delta(snapshots: dict, symbol: str) -> go.Figure:
    """Dual-axis line chart of a position's value and portfolio weight across snapshots."""
    dates, values, weights = [], [], []

    for date_str, df in snapshots.items():
        row = df[df["symbol"] == symbol]
        if not row.empty:
            dates.append(date_str)
            values.append(float(row.iloc[0]["current_value"]))
            weights.append(float(row.iloc[0]["portfolio_weight_pct"]))

    fig = go.Figure([
        go.Scatter(
            name          = "Current Value ($)",
            x             = dates,
            y             = values,
            mode          = "lines+markers",
            line          = dict(color=ACCENT, width=2),
            marker        = dict(size=8),
            yaxis         = "y1",
            hovertemplate = "<b>%{x}</b><br>Value: $%{y:,.2f}<extra></extra>",
        ),
        go.Scatter(
            name          = "Portfolio Weight (%)",
            x             = dates,
            y             = weights,
            mode          = "lines+markers",
            line          = dict(color=MUTED, width=2, dash="dot"),
            marker        = dict(size=8),
            yaxis         = "y2",
            hovertemplate = "<b>%{x}</b><br>Weight: %{y:.1f}%<extra></extra>",
        ),
    ])

    fig.update_layout(
        yaxis  = dict(title="Current Value ($)", gridcolor=GRID, zerolinecolor=GRID),
        yaxis2 = dict(title="Portfolio Weight (%)", overlaying="y", side="right", showgrid=False),
        legend = dict(orientation="h", x=0, y=1.08, font=dict(color=TEXT), bgcolor=BG, bordercolor=GRID),
    )

    return _apply_base(fig, f"{symbol} — Value & Weight Over Time")
