"""The gate must catch a defect that does not affect the whole panel.

An independent cross-family review defeated the first version of this gate by
applying the v3.0 barrier to a single year. Every band was a panel median, so
the good years diluted the bad one and the verdict was PASS. These tests pin
each hole that review opened.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ddpd.models import solve_merton
from ddpd.validate import validate

PANEL = Path(__file__).resolve().parents[1] / "data" / "outputs" / "datasheet" / "dd_pd_panel_corrected.csv"

pytestmark = pytest.mark.skipif(
    not PANEL.exists(), reason="needs the committed panel"
)


@pytest.fixture(scope="module")
def panel():
    frame = pd.read_csv(PANEL)
    return frame[frame["solver_status"] == "converged"].copy()


def _apply_legacy_barrier(frame: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    """Re-solve the masked rows on a v3.0-style barrier, 6% of assets."""
    out = frame.copy()
    for idx in out.index[mask]:
        row = out.loc[idx]
        barrier = row["assets_usd"] * 0.06
        solved = solve_merton(row["E"], row["sigma_E"], barrier, row["rf"])
        if solved is None:
            continue
        out.loc[idx, ["F", "asset_value", "asset_vol", "DD_m", "PD_m",
                      "resid_price", "resid_vol"]] = [
            barrier, solved.asset_value, solved.asset_vol,
            solved.distance_to_default, solved.probability_of_default,
            solved.resid_price, solved.resid_vol,
        ]
    return out


def test_defect_confined_to_one_year_is_caught(panel):
    """2023 is the year US banks failed. It is the worst place to hide this."""
    corrupted = _apply_legacy_barrier(panel, panel["year"] == 2023)
    code, report = validate(corrupted, n_expected=1424)
    assert code == 1, f"a barrier wrong for 2023 alone passed the gate:\n{report}"
    assert "every year within band" in report


def test_panel_median_alone_would_have_missed_it(panel):
    """Documents WHY the per-year check exists, not just that it fires."""
    corrupted = _apply_legacy_barrier(panel, panel["year"] == 2023)
    panel_median = (corrupted["asset_value"] / corrupted["F"]).median()
    year_median = (
        corrupted.loc[corrupted["year"] == 2023, "asset_value"]
        / corrupted.loc[corrupted["year"] == 2023, "F"]
    ).median()
    assert panel_median < 1.30, "the panel median stays inside its band"
    assert year_median > 2.0, "while the corrupted year is far outside it"


def test_defect_in_a_minority_of_years_is_caught(panel):
    corrupted = _apply_legacy_barrier(panel, panel["year"].isin([2021, 2022, 2023]))
    code, _ = validate(corrupted, n_expected=1424)
    assert code == 1


def test_missing_expected_rows_blocks_rather_than_passes(panel):
    """Without the count, the coverage check cannot run; that must not be a pass."""
    code, report = validate(panel)
    assert code == 2, "no row count supplied must be BLOCKED, never PASS"
    assert "coverage" in report


def test_a_missing_interior_year_is_caught(panel):
    """2017 is used because it is interior AND small enough that the coverage
    floor does not trip first; dropping a 200-row year returns BLOCKED on
    coverage before the structural check is ever reached."""
    partial = panel[panel["year"] != 2017]
    code, report = validate(partial, n_expected=1424)
    assert code == 1, "a hole in the middle of the panel must not pass"
    assert "no interior year missing" in report
    assert "2017" in report


def test_a_large_missing_year_blocks_on_coverage(panel):
    """The other route to the same outcome: too thin to judge."""
    partial = panel[panel["year"] != 2020]
    code, _ = validate(partial, n_expected=1424)
    assert code == 2


def test_a_missing_EDGE_year_is_a_known_limit_not_a_pass_to_be_faked(panel):
    """Documents what the gate CANNOT do, so nobody assumes it can.

    Dropping the last year leaves 81.4% coverage and dropping the first leaves
    87.1%; the real panel sits at 91.6%. No floor separates them. Rather than
    tune a threshold until this test goes green, the limit is recorded here and
    the per-year table is where a human sees the year is absent.
    """
    partial = panel[panel["year"] != 2023]
    code, report = validate(partial, n_expected=1424)
    assert code == 0, "if this ever fails, the gate got stronger; update the note"
    assert "2023" not in report.split("Dependent-variable")[0], (
        "the per-year table must make the absence visible to a reader"
    )


@pytest.mark.parametrize("column", ["assets_usd", "sigma_E"])
def test_deleting_a_column_blocks_instead_of_skipping_its_check(panel, column):
    """A producer must not be able to delete a check by deleting a column."""
    code, report = validate(panel.drop(columns=[column]), n_expected=1424)
    assert code == 2, f"dropping {column} returned {code}, not BLOCKED"
    assert column in report


def test_missing_sigma_E_does_not_raise(panel):
    """It used to raise KeyError, which is a crash, not a verdict."""
    validate(panel.drop(columns=["sigma_E"]), n_expected=1424)


def test_unverified_drift_is_caught(panel):
    code, report = validate(panel.drop(columns=["mu_agreement"]), n_expected=1424)
    assert code == 1
    assert "drift" in report.lower()


def test_drift_disagreeing_with_market_cap_is_caught(panel):
    weak = panel.copy()
    weak["mu_agreement"] = 0.30
    code, _ = validate(weak, n_expected=1424)
    assert code == 1


JOINED = PANEL.parent / "esg_dd_pd_latest.csv"


@pytest.mark.skipif(not JOINED.exists(), reason="needs the joined file")
def test_the_joined_file_still_carries_what_the_gate_checks():
    """merging.ipynb runs the gate on its own output before writing it.

    A column added to the gate's required set must also be added to that
    notebook's carry list, or the join silently stops being judged. That
    regression happened once: hardening the gate made the joined file BLOCK on
    a missing `assets_usd`.
    """
    joined = pd.read_csv(JOINED, low_memory=False)
    code, report = validate(joined.dropna(subset=["DD_m"]), n_expected=len(joined))
    assert code == 0, f"the joined file no longer passes its own gate:\n{report}"
