"""Economic acceptance gate for a regenerated DD/PD dataset.

Run as a script; the exit code is the verdict and is what the Archon workflow
reads. Nothing here trusts a summary written by whatever produced the dataset:
every number is recomputed from the CSV itself.

    0  PASS     every band holds
    1  FAIL     at least one band is violated; do not ship this dataset
    2  BLOCKED  the input is too thin or missing to judge; not a code defect

BLOCKED exists so that "the data was not there" is a cheap and honest outcome.
An actor with no way to say that is pushed toward making something up.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import bands


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.failures: list[str] = []
        self.blocked: list[str] = []

    def band(self, name: str, value: float, band: bands.Band) -> None:
        ok = band.holds(value)
        mark = "PASS" if ok else "FAIL"
        self.lines.append(
            f"  [{mark}] {name:34s} {value:>12.4f}   band [{band.low}, {band.high}]"
        )
        if not ok:
            self.failures.append(f"{name} = {value:.4f} outside [{band.low}, {band.high}] : {band.why}")

    def check(self, name: str, ok: bool, detail: str, why: str = "") -> None:
        mark = "PASS" if ok else "FAIL"
        self.lines.append(f"  [{mark}] {name:34s} {detail}")
        if not ok:
            self.failures.append(f"{name}: {detail}{(' : ' + why) if why else ''}")

    def block(self, name: str, detail: str) -> None:
        self.lines.append(f"  [BLOCKED] {name:31s} {detail}")
        self.blocked.append(f"{name}: {detail}")


def _median(frame: pd.DataFrame, expr) -> float:
    series = expr(frame).replace([np.inf, -np.inf], np.nan).dropna()
    return float(series.median()) if len(series) else float("nan")


def validate(frame: pd.DataFrame, n_expected: int | None = None) -> tuple[int, str]:
    """Return ``(exit_code, report_text)`` for a regenerated panel.

    ``n_expected`` is REQUIRED. Without it the coverage check silently does not
    run, and a panel missing an entire year returns PASS; an independent review
    demonstrated exactly that. It is a caller-supplied number, so it is not
    proof on its own, but its absence must not be a free pass.
    """
    rep = Report()
    rep.lines.append("DD/PD ECONOMIC ACCEPTANCE GATE")
    rep.lines.append(f"  rows in file: {len(frame)}")

    # Every column the checks below index. A column absent from this set but
    # used by a check turns a clean BLOCKED into an unhandled KeyError, and a
    # column used only inside an `if col in frame` guard lets a producer delete
    # the check by deleting the column.
    required = {"ticker", "year", "F", "E", "sigma_E", "assets_usd",
                "DD_m", "PD_m", "DD_a", "PD_a",
                "asset_value", "asset_vol", "resid_price", "resid_vol"}
    missing = sorted(required - set(frame.columns))
    if missing:
        rep.block("schema", f"missing columns: {', '.join(missing)}")
        return 2, "\n".join(rep.lines + [""] + [f"BLOCKED: {b}" for b in rep.blocked])

    converged = frame[frame["DD_m"].notna()].copy()
    if n_expected is None:
        rep.block("coverage", "n_expected not supplied; cannot judge missing rows")
        return 2, "\n".join(rep.lines + [""] + [f"BLOCKED: {b}" for b in rep.blocked])
    if True:
        coverage = len(converged) / n_expected
        if coverage < bands.MIN_COVERAGE:
            rep.block("coverage", f"{coverage:.1%} of {n_expected} rows, floor {bands.MIN_COVERAGE:.0%}")
            return 2, "\n".join(rep.lines + [""] + [f"BLOCKED: {b}" for b in rep.blocked])
        rep.lines.append(f"  coverage: {coverage:.1%} of {n_expected} input rows")
    if converged.empty:
        rep.block("rows", "no converged rows to judge")
        return 2, "\n".join(rep.lines + [""] + [f"BLOCKED: {b}" for b in rep.blocked])

    rep.lines.append("")
    rep.lines.append("Economic plausibility (would have caught the v3.0 barrier defect):")
    rep.band("median V/F", _median(converged, lambda d: d["asset_value"] / d["F"]),
             bands.MEDIAN_V_OVER_F)
    rep.band("median sigma_V", _median(converged, lambda d: d["asset_vol"]),
             bands.MEDIAN_SIGMA_V)
    rep.band("median E/F", _median(converged, lambda d: d["E"] / d["F"]),
             bands.MEDIAN_E_OVER_F)
    rep.band("median F/assets",
             _median(converged, lambda d: d["F"] / d["assets_usd"]),
             bands.MEDIAN_F_OVER_ASSETS)

    rep.lines.append("")
    rep.lines.append("Per-year, so a defect confined to one year cannot hide in a median:")
    worst_vf = worst_sv = None
    for year, group in converged.groupby("year"):
        vf = _median(group, lambda d: d["asset_value"] / d["F"])
        sv = _median(group, lambda d: d["asset_vol"])
        if not bands.PER_YEAR_V_OVER_F.holds(vf):
            worst_vf = (year, vf) if worst_vf is None or abs(vf - 1.1) > abs(worst_vf[1] - 1.1) else worst_vf
        if not bands.PER_YEAR_SIGMA_V.holds(sv):
            worst_sv = (year, sv) if worst_sv is None else worst_sv
        flag = "    " if (bands.PER_YEAR_V_OVER_F.holds(vf)
                          and bands.PER_YEAR_SIGMA_V.holds(sv)) else " <- "
        rep.lines.append(f"    {int(year)}  n={len(group):>4}  V/F {vf:>7.4f}  "
                         f"sigma_V {sv:>7.4f}{flag}")
    rep.check("every year within band", worst_vf is None and worst_sv is None,
              "all years in band" if worst_vf is None and worst_sv is None
              else f"worst: {worst_vf or worst_sv}",
              "a barrier wrong for one year passes every panel-wide median")

    rep.lines.append("")
    rep.lines.append("Dependent-variable usability:")
    for col in ("PD_m", "PD_a"):
        series = converged[col].dropna()
        share = float((series > 1e-6).mean()) if len(series) else 0.0
        rep.check(
            f"{col} non-degenerate", share >= bands.MIN_SHARE_PD_ABOVE_1E6,
            f"{share:.1%} above 1e-6, floor {bands.MIN_SHARE_PD_ABOVE_1E6:.0%}",
            "a variable that is zero for nearly every row cannot be regressed on",
        )

    rep.lines.append("")
    rep.lines.append("Numerical integrity:")
    rep.check("solver price residual",
              bool((converged["resid_price"] <= bands.MAX_RESID_PRICE).all()),
              f"max {converged['resid_price'].max():.2e}, tol {bands.MAX_RESID_PRICE:.0e}")
    rep.check("solver vol residual",
              bool((converged["resid_vol"] <= bands.MAX_RESID_VOL).all()),
              f"max {converged['resid_vol'].max():.2e}, tol {bands.MAX_RESID_VOL:.0e}")
    rep.check("sigma_V below sigma_E",
              bool((converged["asset_vol"] < converged["sigma_E"]).all()),
              f"{int((converged['asset_vol'] >= converged['sigma_E']).sum())} violations",
              "a levered firm's assets cannot be more volatile than its equity")

    if "mu_agreement" in frame.columns:
        agreement = float(frame["mu_agreement"].dropna().iloc[0]) if frame["mu_agreement"].notna().any() else float("nan")
        rep.check("drift agrees with market cap",
                  agreement >= bands.MIN_DRIFT_AGREEMENT,
                  f"corr {agreement:.3f}, floor {bands.MIN_DRIFT_AGREEMENT}",
                  "the v3.0 defect was an unverified drift; a log line is not a check")
    else:
        rep.check("drift agreement recorded", False,
                  "column mu_agreement absent",
                  "the drift must carry its own cross-source agreement, not a log line")

    rep.lines.append("")
    rep.lines.append("Panel integrity:")
    dupes = int(frame.duplicated(subset=["ticker", "year"]).sum())
    rep.check("unique (ticker, year)", dupes == 0, f"{dupes} duplicate keys")

    # A missing INTERIOR year is caught here. A missing FIRST or LAST year is
    # NOT, and no coverage floor can catch one either: on this panel, dropping
    # 2023 leaves 81.4% and dropping 2016 leaves 87.1%, both above any floor
    # that still admits the real panel at 91.6%. The per-year table above is
    # where a human sees it. Stated rather than papered over with a tuned floor.
    years = sorted(frame["year"].dropna().astype(int).unique())
    gaps = [y for y in range(years[0], years[-1] + 1) if y not in years] if years else []
    rep.check("no interior year missing", not gaps,
              f"missing: {gaps}" if gaps else f"{years[0]}-{years[-1]} contiguous")

    verdict = 1 if rep.failures else 0
    tail = [""]
    if rep.failures:
        tail.append("FAIL")
        tail += [f"  - {f}" for f in rep.failures]
    else:
        tail.append("PASS: every band holds.")
    return verdict, "\n".join(rep.lines + tail)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--expected-rows", type=int, required=True,
                    help="rows the panel should cover; without it the coverage "
                         "check cannot run and a missing year would pass")
    args = ap.parse_args(argv)

    if not args.dataset.exists():
        print(f"BLOCKED: dataset not found: {args.dataset}")
        return 2

    code, text = validate(pd.read_csv(args.dataset), args.expected_rows)
    print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
