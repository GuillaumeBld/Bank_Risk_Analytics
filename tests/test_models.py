"""Unit tests for the two distance-to-default models."""

import numpy as np
import pytest
from scipy.stats import norm

from ddpd.models import naive_dd, solve_merton


def test_merton_recovers_a_known_firm():
    """Round trip: price a firm forward, then ask the solver to invert it."""
    V, sigma_V, F, rf, T = 1_000.0, 0.20, 600.0, 0.03, 1.0
    srt = sigma_V * np.sqrt(T)
    d1 = (np.log(V / F) + (rf + 0.5 * sigma_V**2) * T) / srt
    d2 = d1 - srt
    E = V * norm.cdf(d1) - F * np.exp(-rf * T) * norm.cdf(d2)
    sigma_E = (V / E) * norm.cdf(d1) * sigma_V

    got = solve_merton(E, sigma_E, F, rf, T)
    assert got is not None
    assert got.asset_value == pytest.approx(V, rel=1e-6)
    assert got.asset_vol == pytest.approx(sigma_V, rel=1e-6)
    assert got.distance_to_default == pytest.approx(d2, abs=1e-6)


def test_merton_dd_is_d2_not_d1():
    """DD uses the (rf - 0.5 sigma^2) drift. Using d1 would overstate it."""
    got = solve_merton(400.0, 0.30, 600.0, 0.03)
    assert got is not None
    expected_d1 = got.distance_to_default + got.asset_vol
    assert expected_d1 > got.distance_to_default
    assert got.probability_of_default == pytest.approx(norm.cdf(-got.distance_to_default))


def test_lower_barrier_raises_distance_to_default():
    """The defect in one assertion: shrink F and DD rises."""
    high = solve_merton(200.0, 0.25, 2_000.0, 0.02)
    low = solve_merton(200.0, 0.25, 200.0, 0.02)
    assert high is not None and low is not None
    assert low.distance_to_default > high.distance_to_default
    assert low.asset_vol > high.asset_vol


@pytest.mark.parametrize(
    "equity,vol,barrier",
    [(0.0, 0.2, 100.0), (-5.0, 0.2, 100.0), (100.0, 0.0, 100.0), (100.0, 0.2, 0.0)],
)
def test_merton_returns_none_on_unusable_input(equity, vol, barrier):
    assert solve_merton(equity, vol, barrier, 0.02) is None


def test_merton_asset_vol_below_equity_vol_for_levered_firm():
    got = solve_merton(150.0, 0.35, 1_000.0, 0.02)
    assert got is not None
    assert got.asset_vol < 0.35


def test_naive_dd_matches_bharath_shumway_by_hand():
    E, sigma_E, F, mu = 100.0, 0.40, 900.0, 0.08
    V = E + F
    sigma_D = 0.05 + 0.25 * sigma_E
    sigma_V = (E / V) * sigma_E + (F / V) * sigma_D
    expected = (np.log(V / F) + (mu - 0.5 * sigma_V**2)) / sigma_V

    dd, pd_, sv = naive_dd([E], [sigma_E], [F], [mu])
    assert sv[0] == pytest.approx(sigma_V)
    assert dd[0] == pytest.approx(expected)
    assert pd_[0] == pytest.approx(norm.cdf(-expected))


def test_naive_dd_is_nan_without_a_drift():
    """No lagged return means no drift; the row must not be silently imputed."""
    dd, _, _ = naive_dd([100.0], [0.3], [900.0], [np.nan])
    assert np.isnan(dd[0])
