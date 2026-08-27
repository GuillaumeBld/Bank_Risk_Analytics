"""Tests for the Fama-French cost of equity."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ddpd.factors import (MIN_MONTHS, cost_of_equity, load_monthly_factors,
                          long_run_premia)

FACTOR_FILE = Path(__file__).resolve().parents[1] / "data" / "clean" / "ff_factors_monthly_raw.csv"


def _factors(n=120, start=201401):
    months = []
    y, m = divmod(start, 100)
    for _ in range(n):
        months.append(y * 100 + m)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return pd.DataFrame({
        "yyyymm": months,
        "mkt_rf": np.linspace(-0.02, 0.03, n),
        "smb": np.zeros(n),
        "hml": np.zeros(n),
        "rf": np.full(n, 0.001),
        "year": [x // 100 for x in months],
        "month": [x % 100 for x in months],
    })


def _returns(factors, beta_mkt):
    """A stock that is exactly beta times the market, with no idiosyncratic noise."""
    return pd.DataFrame({
        "ticker": "AAA",
        "year": factors["year"],
        "month": factors["month"],
        "total_return_pct": (factors["rf"] + beta_mkt * factors["mkt_rf"]) * 100,
    })


def test_beta_is_recovered_from_a_noiseless_stock():
    factors = _factors()
    rf = pd.DataFrame({"year": [2020], "rf": [0.01]})
    out, _ = cost_of_equity(_returns(factors, 1.5), factors, rf, range(2020, 2021))
    assert len(out) == 1
    assert out["ff_beta_mkt"].iloc[0] == pytest.approx(1.5, abs=1e-6)


def test_cost_of_equity_matches_the_formula():
    factors = _factors()
    rf = pd.DataFrame({"year": [2020], "rf": [0.01]})
    out, premia = cost_of_equity(_returns(factors, 1.5), factors, rf, range(2020, 2021))
    row = out.iloc[0]
    expected = (0.01 + row["ff_beta_mkt"] * premia.mkt_rf
                + row["ff_beta_smb"] * premia.smb + row["ff_beta_hml"] * premia.hml)
    assert row["ff_cost_of_equity"] == pytest.approx(expected)


def test_window_ends_before_the_year_being_priced():
    """No lookahead: the same discipline sigma_E follows."""
    factors = _factors()
    rf = pd.DataFrame({"year": [2020], "rf": [0.01]})
    out, _ = cost_of_equity(_returns(factors, 1.0), factors, rf, range(2020, 2021))
    assert out["ff_window_end_year"].iloc[0] == 2019


def test_too_little_history_yields_no_estimate():
    factors = _factors(n=MIN_MONTHS - 1, start=201801)
    rf = pd.DataFrame({"year": [2021], "rf": [0.01]})
    out, _ = cost_of_equity(_returns(factors, 1.0), factors, rf, range(2021, 2022))
    assert out.empty


def test_a_higher_beta_costs_more():
    factors = _factors()
    rf = pd.DataFrame({"year": [2020], "rf": [0.01]})
    low, _ = cost_of_equity(_returns(factors, 0.5), factors, rf, range(2020, 2021))
    high, _ = cost_of_equity(_returns(factors, 2.0), factors, rf, range(2020, 2021))
    assert high["ff_cost_of_equity"].iloc[0] > low["ff_cost_of_equity"].iloc[0]


@pytest.mark.skipif(not FACTOR_FILE.exists(), reason="needs the factor file")
def test_the_real_factor_file_parses_to_monthly_rows_only():
    """Ken French's CSV concatenates several tables; only the first is monthly."""
    frame = load_monthly_factors(FACTOR_FILE)
    assert len(frame) > 1000
    assert frame["month"].between(1, 12).all()
    assert frame["yyyymm"].is_monotonic_increasing
    assert frame["yyyymm"].min() < 193000, "history should start in the 1920s"


@pytest.mark.skipif(not FACTOR_FILE.exists(), reason="needs the factor file")
def test_long_run_premia_match_the_published_values():
    """A sanity anchor: these are textbook numbers, not free parameters."""
    premia = long_run_premia(load_monthly_factors(FACTOR_FILE))
    assert 0.06 < premia.mkt_rf < 0.10, "equity premium near 8% a year"
    assert 0.00 < premia.smb < 0.05
    assert 0.02 < premia.hml < 0.07
