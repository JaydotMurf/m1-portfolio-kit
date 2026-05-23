"""
core/loader.py
--------------
Ingests and normalizes M1 Finance holdings CSV exports.

M1 Export path: Portfolio → Holdings → (overflow menu) → Export
Expected columns: Symbol, Name, Quantity, Avg. Price, Cost Basis,
                  Unrealized Gain ($), Unrealized Gain (%), Value
"""

import datetime
import json
import re
from pathlib import Path

import pandas as pd

try:
    import yfinance as yf
    _YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    _YFINANCE_AVAILABLE = False

_DATE_ISO = re.compile(r"(\d{4}-\d{2}-\d{2})")
_DATE_MDY = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2})-(\d{4})",
    re.IGNORECASE,
)
_MONTH_MAP = {
    m: i + 1
    for i, m in enumerate(
        ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
    )
}

# Maps M1's raw column names to clean internal names
M1_COLUMN_MAP = {
    "Symbol":               "symbol",
    "Name":                 "name",
    "Quantity":             "quantity",
    "Avg. Price":           "avg_price",
    "Cost Basis":           "cost_basis",
    "Unrealized Gain ($)":  "unrealized_gain_dollar",
    "Unrealized Gain (%)":  "unrealized_gain_pct",
    "Value":                "current_value",
}

REQUIRED_COLUMNS = list(M1_COLUMN_MAP.keys())

# Columns that may contain comma-formatted strings like "6,174.96"
COMMA_FORMATTED = ["cost_basis", "unrealized_gain_dollar", "current_value"]

# Columns that are plain numerics
PLAIN_NUMERIC = ["quantity", "avg_price", "unrealized_gain_pct"]

# Sector lookup — loaded once at module scope
_SECTORS_PATH = Path(__file__).parent / "sectors.json"
_SECTOR_MAP = json.loads(_SECTORS_PATH.read_text())


def _get_sector(symbol: str) -> str:
    """Return the sector for a ticker, defaulting to 'Other' if unmapped."""
    return _SECTOR_MAP.get(symbol, "Other")


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Strip commas and currency symbols, then cast to float."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
    )


def load_m1_csv(source) -> pd.DataFrame:
    """
    Load an M1 Finance holdings CSV and return a clean DataFrame.

    Parameters
    ----------
    source : str or file-like
        File path or Streamlit UploadedFile object.

    Returns
    -------
    pd.DataFrame
        Normalized holdings data with derived columns appended.

    Raises
    ------
    ValueError
        If required M1 columns are missing from the file.
    """
    df = pd.read_csv(source)

    # Drop any fully empty rows (M1 sometimes appends a totals row)
    df = df.dropna(how="all").reset_index(drop=True)

    # Validate expected schema
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"File is missing expected M1 columns: {missing}\n"
            f"Found columns: {list(df.columns)}"
        )

    # Rename to internal schema
    df = df.rename(columns=M1_COLUMN_MAP)[list(M1_COLUMN_MAP.values())].copy()

    # Clean numeric types
    for col in COMMA_FORMATTED:
        df[col] = _clean_numeric(df[col])
    for col in PLAIN_NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows where symbol is missing (catches M1 summary rows)
    df = df.dropna(subset=["symbol"]).reset_index(drop=True)

    # Derived columns
    total_value = df["current_value"].sum()
    df["portfolio_weight_pct"] = (df["current_value"] / total_value) * 100
    df["sector"] = df["symbol"].map(_get_sector)

    return df


def portfolio_summary(df: pd.DataFrame) -> dict:
    """
    Compute top-level portfolio metrics from a normalized holdings DataFrame.

    Returns a flat dict suitable for Streamlit st.metric() calls.
    """
    total_cost  = df["cost_basis"].sum()
    total_value = df["current_value"].sum()
    total_gain  = df["unrealized_gain_dollar"].sum()
    total_return_pct = ((total_value - total_cost) / total_cost) * 100 if total_cost else 0

    return {
        "total_value":      total_value,
        "total_cost":       total_cost,
        "total_gain":       total_gain,
        "total_return_pct": total_return_pct,
        "positions":        len(df),
        "winners":          int((df["unrealized_gain_dollar"] > 0).sum()),
        "losers":           int((df["unrealized_gain_dollar"] < 0).sum()),
        "largest_position": df.loc[df["current_value"].idxmax(), "symbol"],
        "best_performer":   df.loc[df["unrealized_gain_pct"].idxmax(), "symbol"],
        "worst_performer":  df.loc[df["unrealized_gain_pct"].idxmin(), "symbol"],
    }


def parse_snapshot_date(filename: str) -> str | None:
    """Return the first parseable date found in a filename as YYYY-MM-DD, or None."""
    m = _DATE_ISO.search(filename)
    if m:
        return m.group(1)
    m = _DATE_MDY.search(filename)
    if m:
        month = _MONTH_MAP[m.group(1).lower()]
        day   = int(m.group(2))
        year  = int(m.group(3))
        return datetime.date(year, month, day).isoformat()
    return None


def load_snapshots(files, date_map: dict) -> dict:
    """
    Load multiple M1 CSV files into a date-keyed dict of DataFrames.

    Parameters
    ----------
    files     : list of file-like objects (each must have a .name attribute)
    date_map  : dict mapping file.name -> 'YYYY-MM-DD'

    Returns
    -------
    dict[str, pd.DataFrame], sorted by date ascending

    Raises
    ------
    ValueError
        If two or more files resolve to the same snapshot date.
    """
    dates = list(date_map.values())
    if len(dates) != len(set(dates)):
        from collections import Counter
        dupes = [d for d, n in Counter(dates).items() if n > 1]
        raise ValueError(
            f"Two or more uploaded files map to the same snapshot date: {dupes}. "
            "Use the date pickers to assign a unique date to each file."
        )
    snapshots = {date_map[f.name]: load_m1_csv(f) for f in files}
    return dict(sorted(snapshots.items()))


def snapshot_diff(snapshots: dict) -> pd.DataFrame:
    """
    Compare the oldest and newest snapshot in a snapshots dict.

    Status column values:
      'held'   — present in both snapshots
      'new'    — only in the newest snapshot
      'closed' — only in the oldest snapshot
    """
    dates = sorted(snapshots.keys())
    cols  = ["symbol", "name", "current_value", "unrealized_gain_pct", "portfolio_weight_pct"]
    old   = snapshots[dates[0]][cols]
    new   = snapshots[dates[-1]][cols]

    m = old.merge(new, on="symbol", how="outer", suffixes=("_old", "_new"))

    m["status"] = "held"
    m.loc[m["current_value_old"].isna(), "status"] = "new"
    m.loc[m["current_value_new"].isna(), "status"] = "closed"

    m["value_change"]     = m["current_value_new"].sub(m["current_value_old"])
    m["return_change_pp"] = m["unrealized_gain_pct_new"].sub(m["unrealized_gain_pct_old"])
    m["weight_change_pp"] = m["portfolio_weight_pct_new"].sub(m["portfolio_weight_pct_old"])
    m["name"]             = m["name_new"].fillna(m["name_old"])

    return (
        m[[
            "symbol", "name", "status",
            "current_value_old", "current_value_new", "value_change",
            "unrealized_gain_pct_old", "unrealized_gain_pct_new", "return_change_pp",
            "portfolio_weight_pct_old", "portfolio_weight_pct_new", "weight_change_pp",
        ]]
        .sort_values(["status", "value_change"], ascending=[True, False])
        .reset_index(drop=True)
    )


def compute_snapshot_change(snapshots: dict) -> dict:
    """
    Summarize the change between the oldest and newest snapshot.

    Parameters
    ----------
    snapshots : dict[str, pd.DataFrame]
        Date-keyed snapshot registry (must contain at least two entries).

    Returns
    -------
    dict with keys:
        delta_dollar      : float — total portfolio value change in dollars
        delta_pct         : float — total portfolio value change as a percentage
        days_elapsed      : int   — calendar days between oldest and newest date
        positions_added   : int   — count of positions in newest but not oldest
        positions_closed  : int   — count of positions in oldest but not newest
    """
    dates = sorted(snapshots.keys())
    old_df = snapshots[dates[0]]
    new_df = snapshots[dates[-1]]

    old_value = old_df["current_value"].sum()
    new_value = new_df["current_value"].sum()
    delta_dollar = new_value - old_value
    delta_pct = (delta_dollar / old_value * 100) if old_value else 0.0

    old_date = datetime.date.fromisoformat(dates[0])
    new_date = datetime.date.fromisoformat(dates[-1])
    days_elapsed = (new_date - old_date).days

    old_symbols = set(old_df["symbol"])
    new_symbols = set(new_df["symbol"])

    return {
        "delta_dollar":     delta_dollar,
        "delta_pct":        delta_pct,
        "days_elapsed":     days_elapsed,
        "positions_added":  len(new_symbols - old_symbols),
        "positions_closed": len(old_symbols - new_symbols),
    }


def fetch_benchmark(tickers: list[str], start: str, end: str) -> dict[str, pd.Series] | None:
    """
    Download historical closing prices for benchmark tickers and return each as a
    % return series normalized from the first available price.

    Parameters
    ----------
    tickers : list of ticker symbols, e.g. ["SPY", "QQQ"]
    start   : start date string 'YYYY-MM-DD'
    end     : end date string 'YYYY-MM-DD'

    Returns
    -------
    dict[str, pd.Series] indexed by pd.Timestamp, values are % return from first price.
    Returns None if yfinance is not installed, the network call fails, or no data is found.
    """
    if not _YFINANCE_AVAILABLE:
        return None
    try:
        raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
        if raw.empty:
            return None
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            close = raw[["Close"]].rename(columns={"Close": tickers[0]})
        result = {}
        for ticker in tickers:
            if ticker not in close.columns:
                continue
            series = close[ticker].dropna()
            if len(series) == 0:
                continue
            result[ticker] = (series / series.iloc[0] - 1) * 100
        return result or None
    except Exception:
        return None
