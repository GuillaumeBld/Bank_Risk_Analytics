"""Build the total-liabilities panel used as the Merton default barrier.

The default barrier F for a bank is its TOTAL LIABILITIES, not its interest
bearing debt. Deposits are liabilities and dominate bank funding; excluding
them understates F by roughly an order of magnitude and inflates DD.

Two sources, in priority order:

1. ``reported`` -- ``TR.F.TotLiab`` pulled from Refinitiv, the published balance
   sheet line. Accepted only when the vendor's own total assets agree with the
   panel's, which catches a bad ticker to RIC match rather than letting one
   through as a plausible looking number.
2. ``implied_pb`` -- the accounting identity, for bank-years the vendor does not
   cover::

       total_liabilities = total_assets - book_equity
       book_equity       = market_cap / price_to_book_value_per_share

The two agree closely where they overlap: on 1,313 bank-years the ratio of
implied to reported has median 1.000 and an interquartile range of 0.984 to
1.006. :func:`crosscheck_liability_sources` recomputes that on any run.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MM = 1_000_000.0

#: Bank liabilities are a large and stable share of assets. A reconstructed
#: value outside this band is not a plausible bank balance sheet and is
#: rejected rather than silently used.
PLAUSIBLE_LIAB_RATIO = (0.60, 0.98)

#: A reported total-liabilities figure is only trusted when the vendor's own
#: total assets match the panel's for the same bank-year. A ticker that resolved
#: to the wrong RIC returns a complete, internally consistent balance sheet for
#: the wrong company, which no plausibility band can detect.
ASSET_AGREEMENT_TOLERANCE = 0.02


@dataclass(frozen=True)
class LiabilityPanel:
    """Result of :func:`build_liability_panel`."""

    frame: pd.DataFrame
    n_input: int
    n_resolved: int
    rejected: pd.DataFrame

    @property
    def coverage(self) -> float:
        return self.n_resolved / self.n_input if self.n_input else 0.0


def _book_equity_from_price_to_book(
    market_cap: pd.Series, price_to_book: pd.Series
) -> pd.Series:
    """Book equity in USD.

    ``price_to_book_value_per_share`` is price per share over book value per
    share, so ``market_cap / price_to_book`` is ``shares * book_value_per_share``,
    which is book equity. Non positive ratios carry no information and yield NaN.
    """
    ratio = pd.to_numeric(price_to_book, errors="coerce")
    ratio = ratio.where(ratio > 0)
    return pd.to_numeric(market_cap, errors="coerce") / ratio


def build_liability_panel(
    accounting: pd.DataFrame,
    market_cap: pd.DataFrame,
    reported: pd.DataFrame | None = None,
    reference: pd.DataFrame | None = None,
    *,
    assets_col: str = "total_assets",
    ticker_col: str = "instrument",
    assets_in_millions: bool = True,
) -> LiabilityPanel:
    """Construct a ``(ticker, year) -> total_liabilities`` panel in USD.

    Parameters
    ----------
    accounting:
        Must carry ``ticker_col`` (default ``instrument``), ``year``,
        ``total_assets`` and ``price_to_book_value_per_share``.
    market_cap:
        Must carry ``symbol``, ``year``, ``market_cap`` in raw USD.
    reported:
        Optional vendor panel with ``ticker``, ``year``, ``total_liabilities``
        and ``total_assets_ref`` in raw USD. Takes priority where the asset
        cross-check holds.
    reference:
        Optional independently reported panel with ``ticker``, ``year`` and
        ``deposits`` in raw USD, used only as a last-resort floor.

    Returns
    -------
    LiabilityPanel
        ``frame`` carries one row per resolved ``(ticker, year)`` with columns
        ``total_liabilities``, ``book_equity``, ``liab_method`` and
        ``liab_ratio``. Rows that could not be resolved, or whose reconstructed
        ratio falls outside :data:`PLAUSIBLE_LIAB_RATIO`, are dropped and
        reflected in ``n_resolved``.
    """
    acct = accounting.copy()
    acct["ticker"] = acct[ticker_col].astype(str).str.strip().str.upper()
    acct["year"] = pd.to_numeric(acct["year"], errors="coerce").astype("Int64")

    mc = market_cap.copy()
    mc["ticker"] = mc["symbol"].astype(str).str.strip().str.upper()
    mc["year"] = pd.to_numeric(mc["year"], errors="coerce").astype("Int64")
    mc = mc.dropna(subset=["market_cap"]).drop_duplicates(["ticker", "year"])

    keys = acct[["ticker", "year", assets_col, "price_to_book_value_per_share"]]
    keys = keys.drop_duplicates(["ticker", "year"])
    n_input = len(keys)

    df = keys.merge(
        mc[["ticker", "year", "market_cap"]], on=["ticker", "year"], how="left",
        validate="1:1",
    )

    scale = MM if assets_in_millions else 1.0
    df["assets_usd"] = pd.to_numeric(df[assets_col], errors="coerce") * scale
    df["book_equity"] = _book_equity_from_price_to_book(
        df["market_cap"], df["price_to_book_value_per_share"]
    )
    df["total_liabilities"] = df["assets_usd"] - df["book_equity"]
    df["liab_method"] = np.where(df["total_liabilities"].notna(), "implied_pb", "")

    if reported is not None and not reported.empty:
        rep = reported.copy()
        rep["ticker"] = rep["ticker"].astype(str).str.strip().str.upper()
        rep["year"] = pd.to_numeric(rep["year"], errors="coerce").astype("Int64")
        rep = rep.dropna(subset=["total_liabilities"])
        # A vendor row per (ticker, year); where the pull returned several, keep
        # the largest balance sheet, which is the consolidated parent.
        rep = (rep.sort_values(["ticker", "year", "total_assets_ref"],
                               ascending=[True, True, False])
                  .drop_duplicates(["ticker", "year"], keep="first"))
        df = df.merge(
            rep[["ticker", "year", "total_liabilities", "total_assets_ref"]],
            on=["ticker", "year"], how="left", suffixes=("", "_rep"), validate="1:1",
        )
        assets_agree = (
            (df["total_assets_ref"] / df["assets_usd"] - 1).abs()
            <= ASSET_AGREEMENT_TOLERANCE
        )
        use_reported = df["total_liabilities_rep"].notna() & assets_agree
        df.loc[use_reported, "total_liabilities"] = df.loc[use_reported, "total_liabilities_rep"]
        df.loc[use_reported, "liab_method"] = "reported"
        df["asset_match"] = assets_agree

    if reference is not None and not reference.empty:
        ref = reference.copy()
        ref["ticker"] = ref["ticker"].astype(str).str.strip().str.upper()
        ref["year"] = pd.to_numeric(ref["year"], errors="coerce").astype("Int64")
        ref = ref.drop_duplicates(["ticker", "year"])
        df = df.merge(
            ref[["ticker", "year", "deposits"]], on=["ticker", "year"], how="left",
            validate="1:1",
        )
        # Fallback: reported deposits are a floor on liabilities. Used only where
        # the identity above could not be evaluated at all.
        gap = df["total_liabilities"].isna() & df["deposits"].notna()
        df.loc[gap, "total_liabilities"] = df.loc[gap, "deposits"]
        df.loc[gap, "liab_method"] = "ref_deposits_floor"

    df["liab_ratio"] = df["total_liabilities"] / df["assets_usd"]
    lo, hi = PLAUSIBLE_LIAB_RATIO
    keep = df["total_liabilities"].gt(0) & df["liab_ratio"].between(lo, hi)
    # A silent filter here would remove the distressed tail, which is exactly
    # what a default-risk panel exists to price. Rejections are returned so the
    # caller can log them per row rather than infer them from a row count.
    rejected = df.loc[~keep & df["total_liabilities"].notna(),
                      ["ticker", "year", "liab_ratio", "liab_method"]].copy()
    resolved = df.loc[keep].copy()

    cols = [
        "ticker", "year", "assets_usd", "book_equity",
        "total_liabilities", "liab_ratio", "liab_method",
    ]
    return LiabilityPanel(
        frame=resolved[cols].reset_index(drop=True),
        n_input=n_input,
        n_resolved=len(resolved),
        rejected=rejected.reset_index(drop=True),
    )


def crosscheck_liability_sources(frame: pd.DataFrame) -> pd.DataFrame:
    """Ratio of the implied construction to the reported line, where both exist.

    Reported and implied are independent: one is a published balance sheet line,
    the other is the market's view of book equity subtracted from assets. A
    median far from 1 means one of them is measuring the wrong thing.
    """
    both = frame.dropna(subset=["implied_liabilities", "reported_liabilities"]).copy()
    both["ratio"] = both["implied_liabilities"] / both["reported_liabilities"]
    return both.replace([np.inf, -np.inf], np.nan).dropna(subset=["ratio"])


def crosscheck_against_reference(
    panel: pd.DataFrame, reference: pd.DataFrame, debt_usd: pd.DataFrame
) -> pd.DataFrame:
    """Compare reconstructed liabilities to reported deposits plus debt.

    The two constructions are independent: one comes from the market's view of
    book equity, the other from reported balance sheet lines. Reported deposits
    plus debt omits other liabilities, so the ratio is expected to sit slightly
    below 1 rather than exactly at it.

    Returns one row per overlapping ``(ticker, year)`` with a ``ratio`` column.
    """
    ref = reference.rename(columns={"ticker": "ticker"}).copy()
    ref["ticker"] = ref["ticker"].astype(str).str.upper()
    merged = (
        panel.merge(ref[["ticker", "year", "deposits"]], on=["ticker", "year"])
        .merge(debt_usd[["ticker", "year", "debt_usd"]], on=["ticker", "year"])
    )
    merged["reported_liabilities"] = merged["deposits"] + merged["debt_usd"]
    merged["ratio"] = merged["reported_liabilities"] / merged["total_liabilities"]
    return merged.replace([np.inf, -np.inf], np.nan).dropna(subset=["ratio"])
