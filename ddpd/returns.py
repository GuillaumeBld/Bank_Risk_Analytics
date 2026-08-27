"""Annual equity returns, compounded from monthly total returns.

WHY THIS EXISTS
---------------
`Book2_clean.csv` carries a `rit` column that is supposed to be the annual
equity return. It is the drift of the Bharath-Shumway model, and `DD_a`
correlates 0.96 with it, so it drives the accounting series almost entirely.

It disagrees with two independent measures of the same quantity:

    monthly-compounded vs change in market cap   corr 0.928
    rit                vs monthly-compounded     corr 0.460
    rit                vs change in market cap   corr 0.403

Two sources agree with each other and disagree with `rit`, which makes `rit`
the outlier rather than the referee. Concretely, JPMorgan returned about 47% in
2019: the monthly file gives 0.4727, the market cap change gives 0.4280, and
`rit` gives 0.1831. For Signature Bank `rit` is not merely wrong but impossible,
reporting -424% and -238% in consecutive years.

So the drift is rebuilt here from `raw_monthly_total_return_2013_2023 (1).csv`,
the same file `scripts/02_calculate_equity_volatility.py` already trusts to
build sigma_E. Using it for the drift as well removes an inconsistency: the
volatility and the drift of the same model now come from the same source.

The monthly file starts in 2013, so a lagged drift is available for 2016, the
first panel year. That recovers rows the `rit` route could not reach.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

#: A partial year would understate the return. Twelve observations or nothing.
REQUIRED_MONTHS = 12


def annual_returns_from_monthly(path: Path) -> pd.DataFrame:
    """Compound monthly total returns into ``(ticker, year) -> annual_return``.

    The source column is a percentage per month. Only complete years are
    returned; ``n_months`` is carried so a caller can see what was dropped.
    """
    monthly = pd.read_csv(path)
    monthly.columns = monthly.columns.str.strip()
    monthly = monthly.rename(columns={
        "Instrument": "instrument", "Date": "date", "Total Return": "total_return_pct",
    })
    monthly["date"] = pd.to_datetime(monthly["date"], errors="coerce", format="mixed")
    monthly = monthly.dropna(subset=["date", "total_return_pct"])
    monthly["year"] = monthly["date"].dt.year
    monthly["ticker"] = (
        monthly["instrument"].astype(str).str.upper().str.split(".").str[0]
    )

    grouped = monthly.groupby(["ticker", "year"])["total_return_pct"]
    out = pd.DataFrame({
        "annual_return": grouped.apply(lambda s: np.prod(1 + s / 100.0) - 1.0),
        "n_months": grouped.size(),
    }).reset_index()
    return out[out["n_months"] == REQUIRED_MONTHS].drop(columns="n_months")


def agreement_with_market_cap(
    returns: pd.DataFrame, market_cap: pd.DataFrame
) -> pd.DataFrame:
    """Compare the compounded return to the year-on-year change in market cap.

    Not a validation gate: market capitalisation moves with share count as well
    as price, so the two are close but not equal. It is a sanity check that the
    compounded series tracks something real, reported in the build log.
    """
    mc = market_cap.rename(columns={"symbol": "ticker"}).copy()
    mc["ticker"] = mc["ticker"].astype(str).str.upper()
    mc = mc.sort_values(["ticker", "year"])
    mc["market_cap_return"] = mc.groupby("ticker")["market_cap"].pct_change(fill_method=None)
    merged = returns.merge(
        mc[["ticker", "year", "market_cap_return"]], on=["ticker", "year"], how="inner"
    )
    return merged.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["annual_return", "market_cap_return"]
    )
