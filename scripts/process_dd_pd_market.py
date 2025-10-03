"""Post-process dd_pd_market results to add logging columns and summaries."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "merged_inputs" / "dd_pd_market.csv"
RESULT_PATH = ROOT / "dd_pd_market.csv"
SUMMARY_PATH = ROOT / "dd_pd_market_summary.csv"

DEFAULT_T = 1.0
DEBT_SCALE = 1_000_000.0
ABS_TOL = 1e-9
REL_TOL = 1e-9


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def is_finite(value: float) -> bool:
    return isinstance(value, (int, float)) and not math.isnan(value) and not math.isinf(value)


def percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return math.nan
    if len(values) == 1:
        return values[0]
    # Linear interpolation between closest ranks.
    k = (len(values) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    low = values[f]
    high = values[c]
    return low * (c - k) + high * (k - f)


def median(values: Sequence[float]) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return 0.5 * (ordered[mid - 1] + ordered[mid])


def format_value(value: object) -> str:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
    if value is None:
        return ""
    return str(value)


def compute_quantile_row(year: str, rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    ddm_values = [row["DDm"] for row in rows if is_finite(row.get("DDm", math.nan))]
    pdm_values = [row["PDm"] for row in rows if is_finite(row.get("PDm", math.nan))]
    ddm_values.sort()
    pdm_values.sort()

    return {
        "year": year,
        "count": len(rows),
        "DDm_min": percentile(ddm_values, 0.0),
        "DDm_p10": percentile(ddm_values, 0.10),
        "DDm_p25": percentile(ddm_values, 0.25),
        "DDm_median": percentile(ddm_values, 0.50),
        "DDm_p75": percentile(ddm_values, 0.75),
        "DDm_p90": percentile(ddm_values, 0.90),
        "DDm_max": percentile(ddm_values, 1.0),
        "PDm_min": percentile(pdm_values, 0.0),
        "PDm_p10": percentile(pdm_values, 0.10),
        "PDm_p25": percentile(pdm_values, 0.25),
        "PDm_median": percentile(pdm_values, 0.50),
        "PDm_p75": percentile(pdm_values, 0.75),
        "PDm_p90": percentile(pdm_values, 0.90),
        "PDm_max": percentile(pdm_values, 1.0),
    }


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Expected input at {INPUT_PATH}")

    with INPUT_PATH.open(newline="") as in_f:
        reader = csv.DictReader(in_f)
        original_fields = list(reader.fieldnames or [])
        processed_rows: List[Dict[str, object]] = []
        barrier_matches = 0
        total_rows = 0

        for row in reader:
            total_rows += 1
            record: Dict[str, object] = dict(row)

            E = to_float(row.get("market_cap", ""))
            sigma_E = to_float(row.get("equity_vol", ""))
            # F convention: using total debt in USD (Option A). Change via config if needed.
            # Input debt is stored in millions, so scale to dollars for the barrier.
            debt_total_raw = to_float(row.get("debt_total", ""))
            F = (
                debt_total_raw * DEBT_SCALE
                if is_finite(debt_total_raw)
                else math.nan
            )
            rf = to_float(row.get("rf", ""))
            T = to_float(row.get("T", ""))
            if not is_finite(T):
                T = DEFAULT_T

            V = to_float(row.get("asset_value", ""))
            sigma_V = to_float(row.get("asset_vol", ""))

            record.update({
                "E": E,
                "sigma_E": sigma_E,
                "F": F,
                "T": T,
                "V": V,
                "sigma_V": sigma_V,
            })

            d1 = math.nan
            d2 = math.nan
            price_implied = math.nan
            vol_implied = math.nan
            resid_price = math.nan
            resid_vol = math.nan

            valid = all(
                is_finite(value) and value > 0
                for value in (E, sigma_E, F, V, sigma_V, T)
            ) and is_finite(rf)

            if valid:
                sqrt_T = math.sqrt(T)
                log_term = math.log(V / F)
                d1 = (log_term + (rf + 0.5 * sigma_V * sigma_V) * T) / (sigma_V * sqrt_T)
                d2 = d1 - sigma_V * sqrt_T
                price_implied = V * norm_cdf(d1) - F * math.exp(-rf * T) * norm_cdf(d2)
                if E != 0:
                    vol_implied = (V / E) * norm_cdf(d1) * sigma_V
                resid_price = price_implied - E
                resid_vol = vol_implied - sigma_E

                ddm_recalc = (  # DDm uses μ = r_f by construction
                    (log_term + (rf - 0.5 * sigma_V * sigma_V) * T) / (sigma_V * sqrt_T)
                )
                ddm_stored = to_float(row.get("DDm", ""))
                if is_finite(ddm_stored):
                    diff = abs(ddm_recalc - ddm_stored)
                    tolerance = 1e-8 + 1e-8 * abs(ddm_stored)
                    if diff > tolerance:
                        raise AssertionError(
                            f"DDm mismatch for instrument {row.get('instrument')} year {row.get('year')}: {ddm_recalc} vs {ddm_stored}"
                        )
                record["DDm"] = ddm_stored if is_finite(ddm_stored) else math.nan
            else:
                record["DDm"] = to_float(row.get("DDm", ""))

            record["d1"] = d1
            record["d2"] = d2
            record["price_implied"] = price_implied
            record["vol_implied"] = vol_implied
            record["resid_price"] = resid_price
            record["resid_vol"] = resid_vol

            pdm_value = to_float(row.get("PDm", ""))
            record["PDm"] = pdm_value if is_finite(pdm_value) else math.nan

            if "solver_message" not in record:
                record["solver_message"] = ""
            if "iterations" not in record:
                record["iterations"] = ""
            if "function_evals" not in record:
                record["function_evals"] = ""

            if is_finite(F) and is_finite(debt_total_raw):
                expected_barrier = debt_total_raw * DEBT_SCALE
                if math.isclose(
                    F,
                    expected_barrier,
                    rel_tol=REL_TOL,
                    abs_tol=ABS_TOL * max(1.0, abs(F)),
                ):
                    barrier_matches += 1

            processed_rows.append(record)

    if total_rows == 0:
        raise ValueError("No rows loaded from input file.")

    barrier_rate = barrier_matches / total_rows
    if barrier_rate < 0.99:
        raise AssertionError(
            f"Barrier convention check failed: {barrier_rate:.2%} < 99%"
        )

    extra_fields = [
        "E",
        "sigma_E",
        "F",
        "T",
        "V",
        "sigma_V",
        "d1",
        "d2",
        "price_implied",
        "vol_implied",
        "resid_price",
        "resid_vol",
        "solver_message",
        "iterations",
        "function_evals",
        "DDm",
        "PDm",
    ]

    fieldnames = original_fields + [
        field for field in extra_fields if field not in original_fields
    ]

    with RESULT_PATH.open("w", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        for record in processed_rows:
            writer.writerow({key: format_value(record.get(key)) for key in fieldnames})

    converged_rows = [
        row for row in processed_rows if str(row.get("solver_status")) == "converged"
    ]
    if not converged_rows:
        raise AssertionError("No converged rows available for summary.")

    if len(converged_rows) != sum(
        1 for row in converged_rows if str(row.get("solver_status")) == "converged"
    ):
        raise AssertionError("Only converged rows must feed the summaries.")

    convergence_rate = len(converged_rows) / total_rows

    abs_price_resids = [
        abs(row["resid_price"]) for row in converged_rows if is_finite(row["resid_price"])
    ]
    abs_vol_resids = [
        abs(row["resid_vol"]) for row in converged_rows if is_finite(row["resid_vol"])
    ]
    median_abs_price = median(abs_price_resids)
    median_abs_vol = median(abs_vol_resids)

    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for row in converged_rows:
        grouped[str(row.get("year"))].append(row)

    summary_rows: List[Dict[str, object]] = []
    for year in sorted(grouped.keys()):
        summary_rows.append(compute_quantile_row(year, grouped[year]))

    summary_rows.append(compute_quantile_row("overall", converged_rows))

    summary_fieldnames = [
        "year",
        "count",
        "DDm_min",
        "DDm_p10",
        "DDm_p25",
        "DDm_median",
        "DDm_p75",
        "DDm_p90",
        "DDm_max",
        "PDm_min",
        "PDm_p10",
        "PDm_p25",
        "PDm_median",
        "PDm_p75",
        "PDm_p90",
        "PDm_max",
    ]

    with SUMMARY_PATH.open("w", newline="") as summary_f:
        writer = csv.DictWriter(summary_f, fieldnames=summary_fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow({key: format_value(row.get(key)) for key in summary_fieldnames})

    print(f"Convergence rate: {convergence_rate:.2%}")
    print(f"Median absolute resid_price: {median_abs_price}")
    print(f"Median absolute resid_vol: {median_abs_vol}")


if __name__ == "__main__":
    main()
