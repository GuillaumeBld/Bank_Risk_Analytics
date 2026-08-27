"""The gate must reject the defect it was written for.

A threshold nobody has seen fail is not a gate. These tests feed the validator
the actual version 3.0 output, which shipped with the understated barrier, and
require a FAIL verdict. Widening a band in ``ddpd/bands.py`` far enough to let
the legacy numbers through will break this file.
"""

from pathlib import Path

import pandas as pd
import pytest

from ddpd.validate import validate

LEGACY = Path(__file__).parent / "fixtures" / "legacy_v3_market_sample.csv"


def _as_gate_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Map the legacy column names onto the schema the gate expects."""
    out = pd.DataFrame({
        "ticker": frame["instrument"].astype(str).str.upper(),
        "year": frame["year"],
        "F": frame["F"],
        "E": frame["market_cap"],
        "sigma_E": frame["equity_vol"],
        "asset_value": frame["asset_value"],
        "asset_vol": frame["asset_vol"],
        "DD_m": frame["DD_m"],
        "PD_m": frame["PD_m"],
        "DD_a": frame["DD_m"],
        "PD_a": frame["PD_m"],
        "resid_price": 0.0,
        "resid_vol": 0.0,
    })
    return out.drop_duplicates(subset=["ticker", "year"])


@pytest.fixture(scope="module")
def legacy():
    return _as_gate_schema(pd.read_csv(LEGACY))


def test_gate_fails_on_legacy_output(legacy):
    code, report = validate(legacy)
    assert code == 1, f"gate passed the known-defective v3.0 dataset:\n{report}"


def test_gate_names_the_barrier_as_the_reason(legacy):
    _, report = validate(legacy)
    assert "median V/F" in report
    assert "FAIL" in report


def test_legacy_leverage_is_implausible(legacy):
    """Documents the defect itself, independent of the gate's thresholds."""
    median_v_over_f = (legacy["asset_value"] / legacy["F"]).median()
    assert median_v_over_f > 3.0, (
        "expected the legacy barrier to imply an absurd V/F near 3.5; "
        f"got {median_v_over_f:.2f}"
    )


def test_legacy_asset_vol_is_equity_like(legacy):
    """sigma_V near sigma_E is the fingerprint of a barrier that hides leverage."""
    assert legacy["asset_vol"].median() > 0.10
