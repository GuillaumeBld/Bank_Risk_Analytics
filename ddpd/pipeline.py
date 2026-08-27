"""Regenerate the DD/PD panel from cleaned inputs.

Barrier convention
------------------
F = TOTAL LIABILITIES, per the project's own methodology note
(``docs/writing/dd_and_pd.md``, "For banks, F = total liabilities"). Deposits
are liabilities and dominate bank funding. The legacy pipeline used
``debt_total``, interest-bearing borrowings only, a median 6.9% of the real
liability stack.

Equity
------
E = observed market capitalisation for BOTH models. The legacy accounting
notebook proxied it as ``price_to_book * (total_assets - debt_total)``, which is
not book equity times price-to-book because the subtrahend is not book equity.
That proxy overstated market cap by a median factor of 8.5.

Measure
-------
DD_m is risk-neutral (drift = rf). DD_a is physical (drift = lagged own return,
per Bharath-Shumway). PD_m and PD_a are therefore NOT comparable in level. Both
are recorded with a ``measure`` column so downstream code cannot forget.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .liabilities import build_liability_panel, crosscheck_against_reference
from .models import naive_dd, solve_merton

MM = 1_000_000.0


@dataclass(frozen=True)
class Inputs:
    accounting: Path
    market_cap: Path
    equity_vol: Path
    risk_free: Path
    reported: Path | None = None
    reference: Path | None = None


def _dedupe(frame: pd.DataFrame, keys: list[str], rule_col: str, label: str,
            log: list[str]) -> pd.DataFrame:
    """Collapse duplicate keys by an explicit, logged rule.

    The legacy merge resolved 127 duplicated bank-years with
    ``drop_duplicates(keep='first')``, so row order decided which figure reached
    the analysis file. Here the rule is stated (largest ``rule_col``) and every
    dropped value is written to the log.
    """
    dupes = frame[frame.duplicated(subset=keys, keep=False)]
    if not dupes.empty:
        for key, group in dupes.groupby(keys):
            values = sorted(group[rule_col].dropna().tolist(), reverse=True)
            log.append(f"{label} {key}: kept {rule_col}={values[0]!r}, dropped {values[1:]!r}")
    ordered = frame.sort_values(keys + [rule_col], ascending=[True] * len(keys) + [False])
    return ordered.drop_duplicates(subset=keys, keep="first").reset_index(drop=True)


def load(inputs: Inputs) -> dict[str, pd.DataFrame]:
    frames = {
        "accounting": pd.read_csv(inputs.accounting),
        "market_cap": pd.read_csv(inputs.market_cap),
        "equity_vol": pd.read_csv(inputs.equity_vol),
        "risk_free": pd.read_csv(inputs.risk_free),
    }
    for name, path in (("reported", inputs.reported), ("reference", inputs.reference)):
        frames[name] = pd.read_csv(path) if path and path.exists() else pd.DataFrame()
    return frames


def build(inputs: Inputs) -> tuple[pd.DataFrame, list[str]]:
    """Return ``(panel, log)``. ``panel`` is one row per ``(ticker, year)``."""
    log: list[str] = []
    raw = load(inputs)

    acct = raw["accounting"].copy()
    acct["ticker"] = acct["instrument"].astype(str).str.strip().str.upper()
    acct["year"] = pd.to_numeric(acct["year"], errors="coerce").astype("Int64")
    acct = acct.dropna(subset=["year"])
    acct = _dedupe(acct, ["ticker", "year"], "total_assets", "accounting", log)
    n_input = len(acct)

    liab = build_liability_panel(
        acct,
        raw["market_cap"],
        ticker_col="ticker",
        reported=raw["reported"] if not raw["reported"].empty else None,
        reference=raw["reference"] if not raw["reference"].empty else None,
    )
    log.append(f"liabilities resolved for {liab.n_resolved}/{liab.n_input} rows "
               f"({liab.coverage:.1%})")
    for method, count in liab.frame["liab_method"].value_counts().items():
        log.append(f"  barrier source {method}: {count} rows")

    if not raw["reference"].empty:
        debt = acct[["ticker", "year"]].copy()
        debt["debt_usd"] = pd.to_numeric(acct["debt_total"], errors="coerce") * MM
        cross = crosscheck_against_reference(liab.frame, raw["reference"], debt)
        if not cross.empty:
            log.append(
                "crosscheck vs reported deposits+debt on "
                f"{len(cross)} rows: ratio median {cross['ratio'].median():.4f}, "
                f"p25 {cross['ratio'].quantile(.25):.4f}, "
                f"p75 {cross['ratio'].quantile(.75):.4f}"
            )

    vol = raw["equity_vol"].rename(columns={"ticker_base": "ticker"}).copy()
    vol["ticker"] = vol["ticker"].astype(str).str.upper()
    vol["year"] = pd.to_numeric(vol["year"], errors="coerce").astype("Int64")
    vol = _dedupe(vol, ["ticker", "year"], "sigma_E_obs_count", "equity_vol", log)

    rf = raw["risk_free"][["year", "rf"]].copy()
    rf["year"] = rf["year"].astype("Int64")
    rf["rf"] = pd.to_numeric(rf["rf"], errors="coerce") / 100.0  # file is in percent

    panel = (
        acct[["ticker", "year", "total_assets", "debt_total", "rit"]]
        .merge(liab.frame, on=["ticker", "year"], how="inner", validate="1:1")
        .merge(vol[["ticker", "year", "sigma_E", "sigma_E_method", "sigma_E_window_months"]],
               on=["ticker", "year"], how="left", validate="1:1")
        .merge(rf, on="year", how="left", validate="m:1")
    )
    # E is the observed market capitalisation, not a proxy derived from it.
    mc = raw["market_cap"].copy()
    mc["ticker"] = mc["symbol"].astype(str).str.upper()
    mc["year"] = pd.to_numeric(mc["year"], errors="coerce").astype("Int64")
    mc = mc.dropna(subset=["market_cap"]).drop_duplicates(["ticker", "year"])
    panel = panel.merge(
        mc[["ticker", "year", "market_cap"]], on=["ticker", "year"], how="left", validate="1:1"
    )
    panel = panel.rename(columns={"market_cap": "E", "total_liabilities": "F"})

    # Time integrity. sigma_E is built from months strictly before January of
    # year t by scripts/02_calculate_equity_volatility.py, so the window ends at
    # t-1 by construction. Record it from the file's own window field rather
    # than asserting a value we just assigned.
    panel["sigmaE_window_months"] = panel["sigma_E_window_months"].fillna(0).astype(int)
    panel["sigmaE_window_end_year"] = panel["year"] - 1
    panel["sigmaE_window_start_year"] = (
        panel["sigmaE_window_end_year"]
        - (panel["sigmaE_window_months"] / 12 - 1).clip(lower=0).astype(int)
    )

    # Physical drift for the naive model: the firm's own lagged annual return.
    panel = panel.sort_values(["ticker", "year"]).reset_index(drop=True)
    panel["mu_hat"] = panel.groupby("ticker")["rit"].shift(1)
    panel["mu_source_year"] = panel["year"] - 1
    # Provenance, and no imputation. Bharath-Shumway's drift is the firm's own
    # lagged return; where there is no prior observation there is no drift, and
    # DD_a is left undefined rather than filled from a peer group. That costs
    # each bank its first panel year (244 rows, one per bank) and is the reason
    # DD_a covers fewer rows than DD_m.
    panel["mu_method"] = np.where(panel["mu_hat"].notna(), "rit_tminus1", "unavailable")

    solvable = (
        panel["E"].gt(0) & panel["F"].gt(0)
        & panel["sigma_E"].between(1e-4, 3.0)
        & panel["rf"].between(-0.10, 0.30)
    )
    log.append(f"{int(solvable.sum())}/{len(panel)} rows pass pre-solve gates")

    for col in ("asset_value", "asset_vol", "DD_m", "PD_m",
                "resid_price", "resid_vol", "nfev"):
        panel[col] = np.nan
    panel["solver_status"] = "not_attempted"

    for idx in panel.index[solvable]:
        row = panel.loc[idx]
        result = solve_merton(row["E"], row["sigma_E"], row["F"], row["rf"])
        if result is None:
            panel.at[idx, "solver_status"] = "no_converge"
            continue
        panel.at[idx, "asset_value"] = result.asset_value
        panel.at[idx, "asset_vol"] = result.asset_vol
        panel.at[idx, "DD_m"] = result.distance_to_default
        panel.at[idx, "PD_m"] = result.probability_of_default
        panel.at[idx, "resid_price"] = result.resid_price
        panel.at[idx, "resid_vol"] = result.resid_vol
        panel.at[idx, "nfev"] = result.nfev
        panel.at[idx, "solver_status"] = "converged"

    dd_a, pd_a, sigma_v_hat = naive_dd(
        panel["E"].to_numpy(), panel["sigma_E"].to_numpy(),
        panel["F"].to_numpy(), panel["mu_hat"].to_numpy(),
    )
    panel["DD_a"], panel["PD_a"], panel["sigma_V_hat"] = dd_a, pd_a, sigma_v_hat

    panel["barrier_convention"] = "total_liabilities"
    panel["equity_source"] = "observed_market_cap"
    panel["measure_m"] = "risk_neutral"
    panel["measure_a"] = "physical"

    converged = int((panel["solver_status"] == "converged").sum())
    log.append(f"merton converged on {converged}/{int(solvable.sum())} attempted rows")
    log.append(f"naive DD computed for {int(np.isfinite(dd_a).sum())} rows")
    return panel, log


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Regenerate the DD/PD panel.")
    ap.add_argument("--clean-dir", type=Path, required=True)
    ap.add_argument("--reported", type=Path, default=None,
                    help="vendor panel carrying total_liabilities and total_assets_ref")
    ap.add_argument("--reference", type=Path, default=None,
                    help="optional fundamentals panel used as a last-resort floor")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--log", type=Path, default=None)
    args = ap.parse_args(argv)

    inputs = Inputs(
        accounting=args.clean_dir / "Book2_clean.csv",
        market_cap=args.clean_dir / "all_banks_marketcap_annual_2016_2023.csv",
        equity_vol=args.clean_dir / "equity_volatility_by_year.csv",
        risk_free=args.clean_dir / "fama_french_factors_annual_clean.csv",
        reported=args.reported,
        reference=args.reference,
    )
    panel, log = build(inputs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.out, index=False)
    text = "\n".join(log)
    print(text)
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text(text + "\n")
    print(f"\nwrote {len(panel)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
