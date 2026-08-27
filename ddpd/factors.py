"""Fama-French three-factor cost of equity, built from monthly data.

WHY THIS EXISTS
---------------
The panel carried a column `FF_Capital` that no script in either repository
computes. Reverse-engineering it against the columns that do exist gives
R-squared 0.95 on a regression whose dominant term is `rit_rf` with a
coefficient near 0.73, so it is a shrunk transformation of the excess return
rather than a cost of capital derived from factor exposures. Two consequences:

1. It correlates 0.972 with `rit_rf` and only 0.63 with a correctly compounded
   annual return, so it inherits the `rit` defect documented in issue #35.
2. Its values run from -42% to +44% with a median of 3.9%. A cost of equity is
   what shareholders require to hold the stock; it cannot be negative for a
   going concern. A series that spends a quarter of its mass below zero is a
   realized excess return wearing a cost-of-capital label.

This module does not attempt to reproduce that column. It builds the textbook
quantity from first principles, with every choice stated.

THE CONSTRUCTION
----------------
For bank i in year t:

    cost_of_equity = rf_t + b_mkt * E[MKT] + b_smb * E[SMB] + b_hml * E[HML]

- Betas come from an OLS regression of the bank's monthly excess return on the
  three monthly factors, over a trailing window ending in December of t-1. Same
  no-lookahead discipline as `sigma_E`.
- The premia E[.] are LONG-RUN means of the monthly factors over the full
  available history, annualised. Using the realised factor return of year t
  instead would make the result a realised return, which is the error the
  legacy column embodies. A cost of capital is an expectation formed before the
  year, not an outcome measured after it.
- `rf_t` is the annual risk-free rate for year t.

The long-run premia are a modelling choice, not a fact. They are recorded on
every row so a reader can see which numbers produced the estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

FACTORS = ["mkt_rf", "smb", "hml"]

#: Months of history required to estimate three betas plus an intercept. Twelve
#: would technically identify the model and would be badly overfitted; three
#: years is the usual floor and matches the sigma_E window.
MIN_MONTHS = 36

#: The window ends in December of t-1, never later.
WINDOW_MONTHS = 60


@dataclass(frozen=True)
class Premia:
    """Annualised long-run factor premia, and the history they came from."""

    mkt_rf: float
    smb: float
    hml: float
    first_month: int
    last_month: int
    n_months: int


def load_monthly_factors(path: Path) -> pd.DataFrame:
    """Read Ken French's monthly factor file.

    The published CSV carries several tables one after another with prose
    between them. The monthly block is the leading run of rows whose first
    field is a six-digit YYYYMM; parsing stops at the first row that is not.
    """
    rows = []
    with open(path, "r", errors="ignore") as handle:
        for line in handle:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 5 or not (parts[0].isdigit() and len(parts[0]) == 6):
                if rows:
                    break          # the monthly block has ended
                continue           # still in the preamble
            try:
                rows.append([int(parts[0])] + [float(p) for p in parts[1:]])
            except ValueError:
                if rows:
                    break
    frame = pd.DataFrame(rows, columns=["yyyymm"] + FACTORS + ["rf"])
    for col in FACTORS + ["rf"]:
        frame[col] = frame[col] / 100.0          # the file is in percent
    frame["year"] = frame["yyyymm"] // 100
    frame["month"] = frame["yyyymm"] % 100
    return frame


def long_run_premia(factors: pd.DataFrame) -> Premia:
    """Annualise the mean monthly factor returns over the whole history."""
    return Premia(
        mkt_rf=float(factors["mkt_rf"].mean()) * 12,
        smb=float(factors["smb"].mean()) * 12,
        hml=float(factors["hml"].mean()) * 12,
        first_month=int(factors["yyyymm"].min()),
        last_month=int(factors["yyyymm"].max()),
        n_months=len(factors),
    )


def _betas(window: pd.DataFrame) -> tuple[float, float, float] | None:
    """OLS of excess return on the three factors. Returns None if unusable."""
    if len(window) < MIN_MONTHS:
        return None
    design = np.column_stack([np.ones(len(window))] + [window[f].to_numpy() for f in FACTORS])
    target = window["excess"].to_numpy()
    if not np.isfinite(design).all() or not np.isfinite(target).all():
        return None
    try:
        coef, *_ = np.linalg.lstsq(design, target, rcond=None)
    except np.linalg.LinAlgError:
        return None
    return float(coef[1]), float(coef[2]), float(coef[3])


def cost_of_equity(
    monthly_returns: pd.DataFrame,
    factors: pd.DataFrame,
    annual_rf: pd.DataFrame,
    years: range,
) -> tuple[pd.DataFrame, Premia]:
    """One row per ``(ticker, year)`` with a Fama-French cost of equity.

    ``monthly_returns`` needs ``ticker``, ``year``, ``month`` and
    ``total_return_pct``. ``annual_rf`` needs ``year`` and ``rf`` as a decimal.
    """
    premia = long_run_premia(factors)

    returns = monthly_returns.copy()
    returns["r"] = pd.to_numeric(returns["total_return_pct"], errors="coerce") / 100.0
    merged = returns.merge(factors[["year", "month"] + FACTORS + ["rf"]],
                           on=["year", "month"], how="inner")
    merged["excess"] = merged["r"] - merged["rf"]
    merged["stamp"] = merged["year"] * 100 + merged["month"]
    merged = merged.dropna(subset=["excess"]).sort_values(["ticker", "stamp"])

    rf_by_year = dict(zip(annual_rf["year"], annual_rf["rf"]))

    out = []
    for ticker, history in merged.groupby("ticker", sort=True):
        for year in years:
            # Strictly before January of `year`: no lookahead, by construction.
            window = history[history["stamp"] < year * 100 + 1].tail(WINDOW_MONTHS)
            beta = _betas(window)
            if beta is None or year not in rf_by_year:
                continue
            b_mkt, b_smb, b_hml = beta
            out.append({
                "ticker": ticker,
                "year": year,
                "ff_cost_of_equity": (
                    rf_by_year[year]
                    + b_mkt * premia.mkt_rf
                    + b_smb * premia.smb
                    + b_hml * premia.hml
                ),
                "ff_beta_mkt": b_mkt,
                "ff_beta_smb": b_smb,
                "ff_beta_hml": b_hml,
                "ff_window_months": len(window),
                "ff_window_end_year": year - 1,
                "ff_premium_mkt": premia.mkt_rf,
                "ff_premium_smb": premia.smb,
                "ff_premium_hml": premia.hml,
            })
    return pd.DataFrame(out), premia
