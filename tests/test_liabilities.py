"""Tests for the total-liabilities reconstruction."""

import pandas as pd
import pytest

from ddpd.liabilities import build_liability_panel, crosscheck_against_reference


def _accounting(**over):
    base = {
        "instrument": ["AAA"], "year": [2020],
        "total_assets": [1_000.0],          # millions
        "price_to_book_value_per_share": [2.0],
    }
    base.update(over)
    return pd.DataFrame(base)


def _market_cap(value=200e6):
    return pd.DataFrame({"symbol": ["AAA"], "year": [2020], "market_cap": [value]})


def test_book_equity_is_market_cap_over_price_to_book():
    """P/B is price per share over book per share, so E/(P/B) is book equity."""
    panel = build_liability_panel(_accounting(), _market_cap(200e6))
    row = panel.frame.iloc[0]
    assert row["book_equity"] == pytest.approx(100e6)       # 200e6 / 2.0
    assert row["total_liabilities"] == pytest.approx(900e6)  # 1000e6 - 100e6
    assert row["liab_method"] == "implied_pb"


def test_implausible_ratio_is_dropped_not_shipped():
    """A firm whose liabilities are 30% of assets is not a bank; drop the row."""
    panel = build_liability_panel(
        _accounting(price_to_book_value_per_share=[0.3]), _market_cap(200e6)
    )
    assert panel.n_resolved == 0
    assert panel.coverage == 0.0


def test_non_positive_price_to_book_yields_no_row():
    panel = build_liability_panel(
        _accounting(price_to_book_value_per_share=[0.0]), _market_cap()
    )
    assert panel.n_resolved == 0


def test_reference_deposits_fill_only_where_identity_fails():
    acct = pd.DataFrame({
        "instrument": ["AAA", "BBB"], "year": [2020, 2020],
        "total_assets": [1_000.0, 1_000.0],
        "price_to_book_value_per_share": [2.0, None],
    })
    mc = pd.DataFrame({"symbol": ["AAA", "BBB"], "year": [2020, 2020],
                       "market_cap": [200e6, 200e6]})
    ref = pd.DataFrame({"ticker": ["AAA", "BBB"], "year": [2020, 2020],
                        "deposits": [1e6, 880e6]})
    panel = build_liability_panel(acct, mc, reference=ref).frame.set_index("ticker")
    assert panel.loc["AAA", "liab_method"] == "implied_pb"
    assert panel.loc["AAA", "total_liabilities"] == pytest.approx(900e6)
    assert panel.loc["BBB", "liab_method"] == "ref_deposits_floor"
    assert panel.loc["BBB", "total_liabilities"] == pytest.approx(880e6)


def test_crosscheck_reports_ratio_against_reported_lines():
    panel = pd.DataFrame({"ticker": ["AAA"], "year": [2020],
                          "total_liabilities": [900e6]})
    ref = pd.DataFrame({"ticker": ["AAA"], "year": [2020], "deposits": [800e6]})
    debt = pd.DataFrame({"ticker": ["AAA"], "year": [2020], "debt_usd": [85e6]})
    out = crosscheck_against_reference(panel, ref, debt)
    assert out["ratio"].iloc[0] == pytest.approx(885 / 900)


def _reported(total_liabilities=900e6, total_assets_ref=1_000e6):
    return pd.DataFrame({
        "ticker": ["AAA"], "year": [2020],
        "total_liabilities": [total_liabilities],
        "total_assets_ref": [total_assets_ref],
    })


def test_reported_line_wins_over_the_implied_construction():
    panel = build_liability_panel(
        _accounting(), _market_cap(200e6), reported=_reported(880e6)
    ).frame.iloc[0]
    assert panel["liab_method"] == "reported"
    assert panel["total_liabilities"] == pytest.approx(880e6)


def test_reported_rejected_when_vendor_assets_disagree():
    """A ticker resolved to the wrong company returns a complete, internally
    consistent balance sheet. Only the asset cross-check catches that."""
    panel = build_liability_panel(
        _accounting(), _market_cap(200e6),
        reported=_reported(total_liabilities=880e6, total_assets_ref=50_000e6),
    ).frame.iloc[0]
    assert panel["liab_method"] == "implied_pb"
    assert panel["total_liabilities"] == pytest.approx(900e6)


def test_implied_fills_where_vendor_has_no_row():
    reported = _reported().iloc[0:0]
    panel = build_liability_panel(
        _accounting(), _market_cap(200e6), reported=reported
    ).frame.iloc[0]
    assert panel["liab_method"] == "implied_pb"


def test_duplicate_vendor_rows_resolve_to_the_consolidated_parent():
    reported = pd.DataFrame({
        "ticker": ["AAA", "AAA"], "year": [2020, 2020],
        "total_liabilities": [400e6, 880e6],
        "total_assets_ref": [450e6, 1_000e6],
    })
    panel = build_liability_panel(
        _accounting(), _market_cap(200e6), reported=reported
    ).frame
    assert len(panel) == 1
    assert panel.iloc[0]["total_liabilities"] == pytest.approx(880e6)
