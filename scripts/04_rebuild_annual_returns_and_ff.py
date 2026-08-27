#!/usr/bin/env python3
"""Rebuild the annual equity return at source, and add a Fama-French cost of equity.

Closes the root cause behind issue #35. The `rit` column is the annual equity
return; it is wrong across the panel and impossible for one bank. Rather than
patch each consumer, this rebuilds the column itself from monthly total returns,
the same source that already supplies `sigma_E`.

The original values are preserved as `rit_legacy` and `rit_rf_legacy`. Nothing
is deleted: a reader comparing old results to new must be able to see what moved.

Adds `ff_cost_of_equity`, the textbook three-factor cost of equity, because the
`FF_Capital` column it replaces was derived from the same broken return. See
ddpd/factors.py for why that column is not reproduced.

    python scripts/04_rebuild_annual_returns_and_ff.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddpd.factors import cost_of_equity, load_monthly_factors  # noqa: E402
from ddpd.returns import annual_returns_from_monthly  # noqa: E402

CLEAN = ROOT / "data" / "clean"
MONTHLY = CLEAN / "raw_monthly_total_return_2013_2023 (1).csv"
FACTORS = CLEAN / "ff_factors_monthly_raw.csv"
RF = CLEAN / "fama_french_factors_annual_clean.csv"

#: Files carrying `rit`. Each is rewritten in place with the legacy values kept.
TARGETS = [
    CLEAN / "Book2_clean.csv",
    CLEAN / "esg_0718_clean.csv",
    ROOT / "data" / "outputs" / "datasheet" / "esg_0718.csv",
]

YEARS = range(2016, 2024)


def _monthly_frame() -> pd.DataFrame:
    frame = pd.read_csv(MONTHLY)
    frame.columns = frame.columns.str.strip()
    frame = frame.rename(columns={
        "Instrument": "instrument", "Date": "date", "Total Return": "total_return_pct",
    })
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce", format="mixed")
    frame = frame.dropna(subset=["date"])
    frame["year"] = frame["date"].dt.year
    frame["month"] = frame["date"].dt.month
    frame["ticker"] = frame["instrument"].astype(str).str.upper().str.split(".").str[0]
    return frame


def main() -> int:
    print("[1] annual returns, compounded from monthly")
    annual = annual_returns_from_monthly(MONTHLY)
    print(f"    {len(annual)} bank-years, {annual['ticker'].nunique()} banks, "
          f"{annual['year'].min()}-{annual['year'].max()}")

    rf = pd.read_csv(RF)[["year", "rf"]].copy()
    rf["rf"] = pd.to_numeric(rf["rf"], errors="coerce") / 100.0

    print("[2] Fama-French cost of equity")
    factors = load_monthly_factors(FACTORS)
    ff, premia = cost_of_equity(_monthly_frame(), factors, rf, YEARS)
    print(f"    factors {premia.first_month}-{premia.last_month}, {premia.n_months} months")
    print(f"    premia annualised  MKT {premia.mkt_rf:.4f}  SMB {premia.smb:.4f}  "
          f"HML {premia.hml:.4f}")
    print(f"    {len(ff)} bank-years estimated")
    print(f"    cost of equity  p10 {ff['ff_cost_of_equity'].quantile(.10):.4f}  "
          f"median {ff['ff_cost_of_equity'].median():.4f}  "
          f"p90 {ff['ff_cost_of_equity'].quantile(.90):.4f}")
    negative = int((ff["ff_cost_of_equity"] < 0).sum())
    print(f"    negative values: {negative}  (a cost of equity below zero is not "
          f"a cost of equity)")

    print("[3] rewriting the source files")
    for path in TARGETS:
        if not path.exists():
            print(f"    SKIP  {path.name} (absent)")
            continue
        frame = pd.read_csv(path, low_memory=False)
        frame["ticker_key"] = frame["instrument"].astype(str).str.upper().str.split(".").str[0]

        if "rit_legacy" in frame.columns:
            print(f"    SKIP  {path.name} (already rebuilt)")
            continue

        frame["rit_legacy"] = pd.to_numeric(frame.get("rit"), errors="coerce")
        frame["rit_rf_legacy"] = pd.to_numeric(frame.get("rit_rf"), errors="coerce")

        merged = frame.merge(
            annual.rename(columns={"annual_return": "_rit_new"}),
            left_on=["ticker_key", "year"], right_on=["ticker", "year"],
            how="left", suffixes=("", "_drop"),
        ).drop(columns=[c for c in ["ticker", "ticker_drop"] if c in frame.columns or True],
               errors="ignore")
        merged = merged.merge(rf.rename(columns={"rf": "_rf"}), on="year", how="left")

        merged["rit"] = merged["_rit_new"]
        merged["rit_rf"] = merged["_rit_new"] - merged["_rf"]
        merged["rit_source"] = np.where(
            merged["_rit_new"].notna(), "monthly_compounded", "unavailable"
        )

        merged = merged.merge(
            ff[["ticker", "year", "ff_cost_of_equity", "ff_beta_mkt", "ff_beta_smb",
                "ff_beta_hml", "ff_window_months"]].rename(columns={"ticker": "_t"}),
            left_on=["ticker_key", "year"], right_on=["_t", "year"], how="left",
        ).drop(columns=["_t", "_rit_new", "_rf", "ticker_key"], errors="ignore")

        merged.to_csv(path, index=False)
        rebuilt = int(merged["rit"].notna().sum())
        moved = int((merged["rit"] - merged["rit_legacy"]).abs().gt(0.10).sum())
        print(f"    {path.name}: {rebuilt}/{len(merged)} rit rebuilt, "
              f"{moved} moved by more than 10 points, "
              f"{int(merged['ff_cost_of_equity'].notna().sum())} with a cost of equity")

    print("\n[4] what changed, on the shared rows")
    book = pd.read_csv(TARGETS[0], low_memory=False)
    both = book.dropna(subset=["rit", "rit_legacy"])
    print(f"    n={len(both)}  correlation legacy vs rebuilt "
          f"{both['rit'].corr(both['rit_legacy']):.4f}")
    print(f"    legacy  min {both['rit_legacy'].min():.4f}  max {both['rit_legacy'].max():.4f}")
    print(f"    rebuilt min {both['rit'].min():.4f}  max {both['rit'].max():.4f}")
    impossible = int((both["rit_legacy"] < -1).sum())
    print(f"    impossible legacy values removed: {impossible}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
