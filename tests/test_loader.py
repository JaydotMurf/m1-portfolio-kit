import io
from unittest.mock import patch
import pandas as pd
import pytest
import plotly.graph_objects as go
from core.loader import (
    load_m1_csv,
    portfolio_summary,
    parse_snapshot_date,
    load_snapshots,
    snapshot_diff,
    fetch_benchmark,
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


# ── Synthetic data ─────────────────────────────────────────────────────────────

# Snapshot 1: AAPL (winner), TSLA (loser), MSFT (winner, comma-formatted)
SAMPLE_CSV = """\
Symbol,Name,Quantity,Avg. Price,Cost Basis,Unrealized Gain ($),Unrealized Gain (%),Value
AAPL,Apple Inc.,10,150.00,1500.00,500.00,33.33,2000.00
TSLA,Tesla Inc.,5,200.00,1000.00,-100.00,-10.00,900.00
MSFT,Microsoft Corp.,8,250.00,"2,000.00","1,000.00",50.00,"3,000.00"
"""

# Snapshot 2: AAPL (held), MSFT (held), NVDA (new) — TSLA closed
SAMPLE_CSV_2 = """\
Symbol,Name,Quantity,Avg. Price,Cost Basis,Unrealized Gain ($),Unrealized Gain (%),Value
AAPL,Apple Inc.,10,170.00,1500.00,1200.00,80.00,2700.00
MSFT,Microsoft Corp.,10,250.00,2500.00,250.00,10.00,2750.00
NVDA,NVIDIA Corp.,5,800.00,3000.00,1000.00,33.33,4000.00
"""


class _NamedStringIO(io.StringIO):
    """StringIO with a .name attribute so load_snapshots can key on it."""
    def __init__(self, data: str, name: str):
        super().__init__(data)
        self.name = name


def make_df():
    return load_m1_csv(io.StringIO(SAMPLE_CSV))


def make_snapshots():
    return {
        "2024-01-01": load_m1_csv(io.StringIO(SAMPLE_CSV)),
        "2024-06-01": load_m1_csv(io.StringIO(SAMPLE_CSV_2)),
    }


# ── Phase 1: loader ────────────────────────────────────────────────────────────

def test_happy_path_shape():
    assert make_df().shape == (3, 9)


def test_happy_path_columns():
    assert set(make_df().columns) == {
        "symbol", "name", "quantity", "avg_price", "cost_basis",
        "unrealized_gain_dollar", "unrealized_gain_pct", "current_value",
        "portfolio_weight_pct",
    }


def test_portfolio_weight_sums_to_100():
    assert make_df()["portfolio_weight_pct"].sum() == pytest.approx(100.0)


def test_comma_formatted_currency():
    msft = make_df()[make_df()["symbol"] == "MSFT"].iloc[0]
    assert msft["cost_basis"]             == pytest.approx(2000.00)
    assert msft["unrealized_gain_dollar"] == pytest.approx(1000.00)
    assert msft["current_value"]          == pytest.approx(3000.00)


def test_negative_gain_loser_count():
    summary = portfolio_summary(make_df())
    assert summary["losers"]  == 1
    assert summary["winners"] == 2


def test_missing_column_raises_with_name():
    bad_csv = """\
Symbol,Name,Quantity,Avg. Price,Cost Basis,Unrealized Gain ($),Unrealized Gain (%)
AAPL,Apple Inc.,10,150.00,1500.00,500.00,33.33
"""
    with pytest.raises(ValueError, match="Value"):
        load_m1_csv(io.StringIO(bad_csv))


# ── Phase 1: charts ────────────────────────────────────────────────────────────

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


# ── Phase 2: parse_snapshot_date ──────────────────────────────────────────────

def test_parse_date_from_prefix():
    assert parse_snapshot_date("2024-01-15_m1_holdings.csv") == "2024-01-15"


def test_parse_date_embedded():
    assert parse_snapshot_date("export_2024-06-01_test.csv") == "2024-06-01"


def test_parse_date_none():
    assert parse_snapshot_date("holdings.csv") is None


# ── Phase 2: load_snapshots ───────────────────────────────────────────────────

def test_load_snapshots_count_and_order():
    files = [
        _NamedStringIO(SAMPLE_CSV_2, "2024-06-01_holdings.csv"),
        _NamedStringIO(SAMPLE_CSV,   "2024-01-01_holdings.csv"),
    ]
    date_map = {f.name: parse_snapshot_date(f.name) for f in files}
    snaps = load_snapshots(files, date_map)
    assert list(snaps.keys()) == ["2024-01-01", "2024-06-01"]


# ── Phase 2: snapshot_diff ────────────────────────────────────────────────────

def test_snapshot_diff_held():
    held = snapshot_diff(make_snapshots())
    held = held[held["status"] == "held"]
    assert set(held["symbol"]) == {"AAPL", "MSFT"}


def test_snapshot_diff_new():
    new = snapshot_diff(make_snapshots())
    new = new[new["status"] == "new"]
    assert list(new["symbol"]) == ["NVDA"]


def test_snapshot_diff_closed():
    closed = snapshot_diff(make_snapshots())
    closed = closed[closed["status"] == "closed"]
    assert list(closed["symbol"]) == ["TSLA"]


def test_snapshot_diff_value_change():
    diff = snapshot_diff(make_snapshots())
    aapl = diff[diff["symbol"] == "AAPL"].iloc[0]
    # AAPL old value = 2000, new value = 2700
    assert aapl["value_change"] == pytest.approx(700.0)


# ── Phase 2: charts ───────────────────────────────────────────────────────────

def test_plot_portfolio_timeline_returns_figure():
    assert isinstance(plot_portfolio_timeline(make_snapshots()), go.Figure)


def test_plot_position_delta_held_symbol():
    assert isinstance(plot_position_delta(make_snapshots(), "AAPL"), go.Figure)


def test_plot_position_delta_closed_symbol():
    # TSLA only in first snapshot — should still return a valid figure
    assert isinstance(plot_position_delta(make_snapshots(), "TSLA"), go.Figure)


# ── Phase 3: fetch_benchmark ──────────────────────────────────────────────────

def _make_bench_df():
    """Synthetic yfinance-style MultiIndex response for SPY + QQQ."""
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    arrays = [["Close", "Close"], ["SPY", "QQQ"]]
    cols = pd.MultiIndex.from_arrays(arrays)
    data = [
        [400.0, 300.0],
        [404.0, 303.0],
        [408.0, 306.0],
        [412.0, 309.0],
        [416.0, 312.0],
    ]
    return pd.DataFrame(data, index=idx, columns=cols)


def test_fetch_benchmark_returns_pct_series():
    with patch("core.loader._YFINANCE_AVAILABLE", True), \
         patch("core.loader.yf") as mock_yf:
        mock_yf.download.return_value = _make_bench_df()
        result = fetch_benchmark(["SPY", "QQQ"], "2024-01-01", "2024-01-07")
    assert isinstance(result, dict)
    assert set(result.keys()) == {"SPY", "QQQ"}
    assert result["SPY"].iloc[0] == pytest.approx(0.0)
    assert result["SPY"].iloc[-1] == pytest.approx(4.0)


def test_fetch_benchmark_network_error_returns_none():
    with patch("core.loader._YFINANCE_AVAILABLE", True), \
         patch("core.loader.yf") as mock_yf:
        mock_yf.download.side_effect = Exception("timeout")
        assert fetch_benchmark(["SPY"], "2024-01-01", "2024-01-07") is None


def test_fetch_benchmark_unavailable_returns_none():
    with patch("core.loader._YFINANCE_AVAILABLE", False):
        assert fetch_benchmark(["SPY"], "2024-01-01", "2024-01-07") is None


def test_plot_portfolio_timeline_with_benchmarks_returns_figure():
    bench_series = pd.Series(
        [0.0, 2.5, 5.0],
        index=pd.to_datetime(["2024-01-01", "2024-01-15", "2024-06-01"]),
    )
    fig = plot_portfolio_timeline(make_snapshots(), {"SPY": bench_series})
    assert isinstance(fig, go.Figure)
