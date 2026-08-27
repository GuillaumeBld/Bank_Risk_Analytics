"""Tests for the annual-return reconstruction that supplies the naive drift."""

import numpy as np
import pandas as pd
import pytest

from ddpd.models import PLAUSIBLE_DRIFT, naive_dd
from ddpd.returns import annual_returns_from_monthly


def _monthly(tmp_path, rows):
    path = tmp_path / "monthly.csv"
    pd.DataFrame(rows, columns=["Instrument", "Date", "Total Return"]).to_csv(
        path, index=False
    )
    return path


def test_compounds_rather_than_sums(tmp_path):
    """Twelve months of +1% is 12.68%, not 12%."""
    rows = [("AAA.O", f"2020-{m:02d}-28", 1.0) for m in range(1, 13)]
    out = annual_returns_from_monthly(_monthly(tmp_path, rows))
    assert out["annual_return"].iloc[0] == pytest.approx(1.01 ** 12 - 1)


def test_partial_year_is_dropped(tmp_path):
    """Eleven months would understate the year; return nothing instead."""
    rows = [("AAA.O", f"2020-{m:02d}-28", 1.0) for m in range(1, 12)]
    assert annual_returns_from_monthly(_monthly(tmp_path, rows)).empty


def test_ticker_suffix_is_stripped(tmp_path):
    rows = [("AAA.OQ", f"2020-{m:02d}-28", 0.0) for m in range(1, 13)]
    out = annual_returns_from_monthly(_monthly(tmp_path, rows))
    assert out["ticker"].iloc[0] == "AAA"


def test_a_year_can_lose_value(tmp_path):
    rows = [("AAA.O", f"2020-{m:02d}-28", -5.0) for m in range(1, 13)]
    out = annual_returns_from_monthly(_monthly(tmp_path, rows))
    assert out["annual_return"].iloc[0] == pytest.approx(0.95 ** 12 - 1)
    assert out["annual_return"].iloc[0] > -1.0, "compounding can approach -100%, never pass it"


@pytest.mark.parametrize("drift", [-4.2356, -2.3767, -1.5, -1.0])
def test_impossible_return_yields_no_dd(drift):
    """A shareholder cannot lose more than the position.

    Book2_clean.csv reports -4.2356 for SBNY 2018. Feeding it through produced
    a DD_a of -29.7, the worst value in the shipped panel.
    """
    dd, _, _ = naive_dd([1e9], [0.25], [9e9], [drift])
    assert np.isnan(dd[0])


def test_plausible_return_still_yields_a_dd():
    dd, _, _ = naive_dd([1e9], [0.25], [9e9], [-0.35])
    assert np.isfinite(dd[0])


def test_drift_band_brackets_reality():
    lo, hi = PLAUSIBLE_DRIFT
    assert lo > -1.0, "a return of exactly -100% is a total wipeout, not a drift"
    assert hi >= 1.0, "a bank can more than double in a year"
