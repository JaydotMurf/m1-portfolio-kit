import io
import pytest
import plotly.graph_objects as go
from core.loader import load_m1_csv, portfolio_summary
from charts.chart_engine import (
    plot_allocation,
    plot_gainloss_dollar,
    plot_gainloss_pct,
    plot_cost_vs_value,
    plot_return_vs_weight,
)

# 3 positions: 2 winners, 1 loser; row 3 uses comma-formatted currency
SAMPLE_CSV = """\
Symbol,Name,Quantity,Avg. Price,Cost Basis,Unrealized Gain ($),Unrealized Gain (%),Value
AAPL,Apple Inc.,10,150.00,1500.00,500.00,33.33,2000.00
TSLA,Tesla Inc.,5,200.00,1000.00,-100.00,-10.00,900.00
MSFT,Microsoft Corp.,8,250.00,"2,000.00","1,000.00",50.00,"3,000.00"
"""


def make_df():
    return load_m1_csv(io.StringIO(SAMPLE_CSV))


def test_happy_path_shape():
    df = make_df()
    assert df.shape == (3, 9)


def test_happy_path_columns():
    df = make_df()
    assert set(df.columns) == {
        "symbol", "name", "quantity", "avg_price", "cost_basis",
        "unrealized_gain_dollar", "unrealized_gain_pct", "current_value",
        "portfolio_weight_pct",
    }


def test_portfolio_weight_sums_to_100():
    df = make_df()
    assert df["portfolio_weight_pct"].sum() == pytest.approx(100.0)


def test_comma_formatted_currency():
    df = make_df()
    msft = df[df["symbol"] == "MSFT"].iloc[0]
    assert msft["cost_basis"] == pytest.approx(2000.00)
    assert msft["unrealized_gain_dollar"] == pytest.approx(1000.00)
    assert msft["current_value"] == pytest.approx(3000.00)


def test_negative_gain_loser_count():
    summary = portfolio_summary(make_df())
    assert summary["losers"] == 1
    assert summary["winners"] == 2


def test_missing_column_raises_with_name():
    bad_csv = """\
Symbol,Name,Quantity,Avg. Price,Cost Basis,Unrealized Gain ($),Unrealized Gain (%)
AAPL,Apple Inc.,10,150.00,1500.00,500.00,33.33
"""
    with pytest.raises(ValueError, match="Value"):
        load_m1_csv(io.StringIO(bad_csv))


def test_plot_allocation_returns_figure():
    assert isinstance(plot_allocation(make_df()), go.Figure)


def test_plot_gainloss_dollar_returns_figure():
    assert isinstance(plot_gainloss_dollar(make_df()), go.Figure)


def test_plot_gainloss_pct_returns_figure():
    assert isinstance(plot_gainloss_pct(make_df()), go.Figure)


def test_plot_cost_vs_value_returns_figure():
    assert isinstance(plot_cost_vs_value(make_df()), go.Figure)


def test_plot_return_vs_weight_returns_figure():
    assert isinstance(plot_return_vs_weight(make_df()), go.Figure)
