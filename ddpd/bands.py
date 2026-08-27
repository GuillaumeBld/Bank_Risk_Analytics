"""Frozen acceptance bands for the DD/PD output.

WHY THIS FILE EXISTS
--------------------
Version 3.0 of this pipeline shipped with a 100% solver convergence rate and
90.6% coverage, both true, while the default barrier was understated roughly
fourteen fold. Convergence measures solver health. Coverage measures row counts.
Neither can see a mis-specified input, so both stayed green through the defect.

These bands measure the ECONOMICS of the output instead, and the legacy numbers
fail every one of them. ``tests/test_bands_reject_legacy.py`` pins that: it
feeds the pre-fix figures to the validator and requires a FAIL. A band widened
far enough to pass the old barrier breaks that test.

CHANGING A BAND
---------------
This module is deliberately outside the write scope of any agent regenerating
the dataset. The Archon workflow refuses to accept a run whose diff touches
this file or ``validate.py`` and escalates to human approval instead. Widen a
band only with a cited reason in the commit message.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Band:
    low: float
    high: float
    what: str
    why: str

    def holds(self, value: float) -> bool:
        return self.low <= value <= self.high


#: Assets over liabilities for a US bank holding company. Equity is 8-13% of
#: assets, so the ratio sits just above 1. The legacy run reported 3.56.
MEDIAN_V_OVER_F = Band(
    1.02, 1.30,
    "median asset value over default barrier",
    "banks are levered ~10:1; a ratio above 1.3 is not a bank balance sheet",
)

#: Asset volatility for a bank, distinct from equity volatility. The literature
#: puts it in the low single digits of a percent. The legacy run reported 0.179,
#: an equity-like number, the signature of a barrier that hides the leverage.
MEDIAN_SIGMA_V = Band(
    0.005, 0.080,
    "median asset volatility",
    "bank asset volatility is 1-5%; an equity-like value means F is too small",
)

#: Market equity over the barrier. Equity is a thin slice of a bank.
MEDIAN_E_OVER_F = Band(
    0.02, 0.35,
    "median market equity over default barrier",
    "equity is a small fraction of bank liabilities",
)

#: A dependent variable that is zero to machine precision for nearly every row
#: carries no cross sectional information. The legacy PD_a was below 1e-10 for
#: 95% of the sample, which makes every PD regression an estimate on a constant.
MIN_SHARE_PD_ABOVE_1E6 = 0.10

#: Below this, the panel is too thin to be worth shipping; the run reports
#: BLOCKED rather than failing, because thin input is not a defect in the code.
MIN_COVERAGE = 0.80

#: Solver residuals. Loose enough for the optimiser's own tolerance, tight
#: enough that a genuinely unconverged row cannot pass as converged.
MAX_RESID_PRICE = 1e-6
MAX_RESID_VOL = 1e-4
