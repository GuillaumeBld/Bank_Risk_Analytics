"""Locating inputs and the panel, shared by the notebooks.

The notebooks are documentation and diagnostics. The computation lives in
:mod:`ddpd.pipeline`; this module is only how a notebook finds it.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .pipeline import Inputs, build

PANEL_NAME = "dd_pd_panel_corrected.csv"


def repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return start


def default_inputs(root: Path | None = None) -> Inputs:
    clean = (root or repo_root()) / "data" / "clean"
    return Inputs(
        accounting=clean / "Book2_clean.csv",
        market_cap=clean / "all_banks_marketcap_annual_2016_2023.csv",
        equity_vol=clean / "equity_volatility_by_year.csv",
        risk_free=clean / "fama_french_factors_annual_clean.csv",
        reported=clean / "total_liabilities_by_year.csv",
    )


def panel_path(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / "data" / "outputs" / "datasheet" / PANEL_NAME


def load_or_build(root: Path | None = None, rebuild: bool = False):
    """Return ``(panel, log)``.

    Reads the committed panel unless it is missing or ``rebuild`` is set, so a
    notebook opened for reading does not spend a minute in the solver. Pass
    ``rebuild=True`` to recompute from ``data/clean/``.
    """
    root = root or repo_root()
    path = panel_path(root)
    if path.exists() and not rebuild:
        return pd.read_csv(path), [f"loaded {path.relative_to(root)}"]
    panel, log = build(default_inputs(root))
    path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(path, index=False)
    return panel, log + [f"wrote {path.relative_to(root)}"]
