"""
core/loader.py
--------------
Ingests and normalizes M1 Finance holdings CSV exports.

M1 Export path: Portfolio → Holdings → (overflow menu) → Export
Expected columns: Symbol, Name, Quantity, Avg. Price, Cost Basis,
                  Unrealized Gain ($), Unrealized Gain (%), Value
"""

import pandas as pd

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
