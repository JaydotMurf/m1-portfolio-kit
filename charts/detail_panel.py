"""
charts/detail_panel.py
----------------------
Per-position visualization functions for the click-to-detail panel.
All plot functions accept a snapshots dict and a symbol string and return
a go.Figure. They handle sparse data (symbol absent from some snapshots).
"""

import plotly.graph_objects as go
from charts.chart_engine import (
    ACCENT, MUTED, GREEN, RED, GRID, TEXT, BG, FONT,
    _apply_base,
)


def _position_series(snapshots: dict, symbol: str, column: str) -> tuple[list, list]:
    dates, values = [], []
    for date_str in sorted(snapshots.keys()):
        df = snapshots[date_str]
        row = df[df["symbol"] == symbol]
        if not row.empty:
            dates.append(date_str)
            values.append(float(row.iloc[0][column]))
    return dates, values


def plot_position_value(snapshots: dict, symbol: str) -> go.Figure:
    """Line chart of a position's current value across snapshots."""
    dates, values = _position_series(snapshots, symbol, "current_value")
    fig = go.Figure(go.Scatter(
        x             = dates,
        y             = values,
        mode          = "lines+markers",
        line          = dict(color=ACCENT, width=2),
        marker        = dict(size=8, color=ACCENT),
        hovertemplate = "<b>%{x}</b><br>Value: $%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title=None, yaxis_title="Value ($)")
    return _apply_base(fig, f"{symbol} — Value Over Time", height=280)


def plot_position_cost(snapshots: dict, symbol: str) -> go.Figure:
    """Line chart of a position's cost basis across snapshots."""
    dates, values = _position_series(snapshots, symbol, "cost_basis")
    fig = go.Figure(go.Scatter(
        x             = dates,
        y             = values,
        mode          = "lines+markers",
        line          = dict(color=MUTED, width=2),
        marker        = dict(size=8, color=MUTED),
        hovertemplate = "<b>%{x}</b><br>Cost Basis: $%{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title=None, yaxis_title="Cost Basis ($)")
    return _apply_base(fig, f"{symbol} — Cost Basis Trend", height=280)


def plot_position_quantity(snapshots: dict, symbol: str) -> go.Figure:
    """Bar chart of a position's quantity at each snapshot."""
    dates, values = _position_series(snapshots, symbol, "quantity")
    fig = go.Figure(go.Bar(
        x             = dates,
        y             = values,
        marker_color  = ACCENT,
        hovertemplate = "<b>%{x}</b><br>Quantity: %{y:.4f}<extra></extra>",
    ))
    fig.update_layout(xaxis_title=None, yaxis_title="Quantity")
    return _apply_base(fig, f"{symbol} — Quantity Changes", height=280)
