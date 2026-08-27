"""Distance-to-default models: Merton (market) and Bharath-Shumway (accounting).

Both take the default barrier ``F`` as an explicit argument. Nothing in this
module decides what F means; that is the caller's choice, made once in
:mod:`ddpd.pipeline` and recorded in the output provenance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import norm

Phi = norm.cdf

#: A total return below -100% is impossible: a shareholder cannot lose more
#: than the position. Book2_clean.csv contains two such values (SBNY 2018 at
#: -4.236 and SBNY 2019 at -2.377), and because DD_a correlates 0.96 with its
#: drift, feeding them through produced the two worst DD_a values in the panel,
#: -29.7 and -17.0. The legacy notebook printed a warning about this and used
#: the value anyway. Rows outside this range get no DD_a.
PLAUSIBLE_DRIFT = (-0.99, 3.0)

#: d1/d2 beyond this are numerically saturated; Phi is 0 or 1 to machine
#: precision either way, and clipping avoids overflow warnings in exp.
_D_CLIP = 35.0


def _d1_d2(V: float, F: float, rf: float, sigma_V: float, T: float):
    srt = sigma_V * np.sqrt(T)
    d1 = (np.log(V / F) + (rf + 0.5 * sigma_V * sigma_V) * T) / srt
    d2 = d1 - srt
    return np.clip(d1, -_D_CLIP, _D_CLIP), np.clip(d2, -_D_CLIP, _D_CLIP)


@dataclass(frozen=True)
class MertonSolution:
    asset_value: float
    asset_vol: float
    distance_to_default: float
    probability_of_default: float
    resid_price: float
    resid_vol: float
    nfev: int


def solve_merton(
    equity: float,
    equity_vol: float,
    barrier: float,
    risk_free: float,
    T: float = 1.0,
) -> MertonSolution | None:
    """Solve the two Merton equations for asset value and asset volatility.

    Equity is a call option on the firm's assets struck at the barrier::

        E      = V*Phi(d1) - F*exp(-rf*T)*Phi(d2)
        sigma_E = (V/E) * Phi(d1) * sigma_V

    Returns ``None`` when inputs are not usable or the optimiser fails, so the
    caller records a non-convergence rather than a fabricated number.

    The distance to default reported is ``d2``, the risk-neutral distance, and
    ``PD = Phi(-d2)`` is therefore a risk-neutral probability.
    """
    if not (equity > 0 and equity_vol > 0 and barrier > 0):
        return None
    if not np.isfinite([equity, equity_vol, barrier, risk_free]).all():
        return None

    def residuals(theta):
        V, sigma_V = np.exp(theta)
        d1, d2 = _d1_d2(V, barrier, risk_free, sigma_V, T)
        model_equity = V * Phi(d1) - barrier * np.exp(-risk_free * T) * Phi(d2)
        # Guard the division: an intermediate iterate can drive model_equity to
        # zero even though the solution does not.
        model_vol = (V / max(model_equity, 1e-12)) * Phi(d1) * sigma_V
        return np.array([
            (model_equity - equity) / max(equity, 1.0),
            model_vol - equity_vol,
        ])

    start = np.log([
        max(equity + barrier, 1.001 * barrier),
        min(max(equity_vol, 1e-3), 1.5),
    ])
    bounds = (
        np.log([1.001 * barrier, 1e-4]),
        np.log([1e3 * (equity + barrier), 3.0]),
    )

    fit = least_squares(
        residuals, start, method="trf", bounds=bounds,
        ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=1000,
    )
    if not fit.success:
        return None

    V, sigma_V = (float(x) for x in np.exp(fit.x))
    resid_price, resid_vol = residuals(fit.x)
    srt = sigma_V * np.sqrt(T)
    dd = float(np.clip(
        (np.log(V / barrier) + (risk_free - 0.5 * sigma_V**2) * T) / srt,
        -_D_CLIP, _D_CLIP,
    ))
    return MertonSolution(
        asset_value=V,
        asset_vol=sigma_V,
        distance_to_default=dd,
        probability_of_default=float(Phi(-dd)),
        resid_price=float(abs(resid_price)),
        resid_vol=float(abs(resid_vol)),
        nfev=int(fit.nfev),
    )


def naive_dd(
    equity: np.ndarray,
    equity_vol: np.ndarray,
    barrier: np.ndarray,
    drift: np.ndarray,
    T: float = 1.0,
):
    """Bharath and Shumway (2008) naive distance to default. No solver.

    The proxies are theirs verbatim::

        V_hat       = E + F
        sigma_D_hat = 0.05 + 0.25 * sigma_E
        sigma_V_hat = (E/V)*sigma_E + (F/V)*sigma_D_hat
        mu_hat      = r_{i,t-1}                (the firm's own lagged return)

    ``mu_hat`` is a physical-measure drift, so the resulting PD is a physical
    probability and is NOT comparable in level to the risk-neutral PD from
    :func:`solve_merton`.

    A drift outside :data:`PLAUSIBLE_DRIFT` is treated as unusable rather than
    clipped: an impossible return is a broken input, and clipping it would
    invent a number for a bank-year we cannot measure.

    Returns ``(dd, pd_, sigma_V_hat)``, each NaN where inputs are unusable.
    """
    E = np.asarray(equity, dtype=float)
    sE = np.asarray(equity_vol, dtype=float)
    F = np.asarray(barrier, dtype=float)
    mu = np.asarray(drift, dtype=float)

    V = E + F
    lo, hi = PLAUSIBLE_DRIFT
    ok = (
        (E > 0) & (F > 0) & (sE > 0)
        & np.isfinite(V) & (V > 0)
        & np.isfinite(mu) & (mu >= lo) & (mu <= hi)
    )

    sigma_D = 0.05 + 0.25 * sE
    with np.errstate(invalid="ignore", divide="ignore"):
        sigma_V = np.where(ok, (E / V) * sE + (F / V) * sigma_D, np.nan)
        dd = np.where(
            ok & (sigma_V > 0),
            (np.log(V / F) + (mu - 0.5 * sigma_V**2) * T) / (sigma_V * np.sqrt(T)),
            np.nan,
        )
    dd = np.clip(dd, -_D_CLIP, _D_CLIP)
    return dd, Phi(-dd), sigma_V
