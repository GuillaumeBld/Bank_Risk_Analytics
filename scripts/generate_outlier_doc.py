#!/usr/bin/env python3
"""Generate the docs/reference/outlier.md report from merged DD/PD inputs."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTING_CSV = ROOT / "data" / "merged_inputs" / "dd_pd_accounting.csv"
MARKET_CSV = ROOT / "data" / "merged_inputs" / "dd_pd_market.csv"
OUTPUT_MD = ROOT / "docs" / "reference" / "outlier.md"
OUTLIER_THRESHOLD = 13.0


@dataclass
class Record:
    instrument: str
    year: int
    dda: Optional[float] = None
    pda: Optional[float] = None
    ddm: Optional[float] = None
    pdm: Optional[float] = None
    acct_wacc_cost: Optional[float] = None
    acct_wacc_weight: Optional[float] = None
    acct_debt_total: Optional[float] = None
    acct_de_ratio: Optional[float] = None
    market_wacc_cost: Optional[float] = None
    market_wacc_weight: Optional[float] = None
    market_debt_total: Optional[float] = None
    market_de_ratio: Optional[float] = None


def parse_float(value: str) -> Optional[float]:
    value = (value or "").strip()
    if not value:
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    if math.isnan(result):
        return None
    return result


def load_records() -> Dict[Tuple[str, int], Record]:
    records: Dict[Tuple[str, int], Record] = {}

    with ACCOUNTING_CSV.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                year = int(float(row.get("year", "")))
            except ValueError:
                continue
            key = (row["instrument"], year)
            record = records.get(key)
            if record is None:
                record = Record(instrument=key[0], year=year)
                records[key] = record

            dda = parse_float(row.get("DDa"))
            pda = parse_float(row.get("PDa"))
            if dda is not None:
                record.dda = dda
            if pda is not None:
                record.pda = pda
            record.acct_wacc_cost = parse_float(row.get("wacc_cost_of_debt,_(%)"))
            record.acct_wacc_weight = parse_float(row.get("wacc_debt_weight,_(%)"))
            record.acct_debt_total = parse_float(row.get("debt_total"))
            record.acct_de_ratio = parse_float(row.get("d/e"))

    with MARKET_CSV.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                year = int(float(row.get("year", "")))
            except ValueError:
                continue
            key = (row["instrument"], year)
            record = records.get(key)
            if record is None:
                record = Record(instrument=key[0], year=year)
                records[key] = record

            ddm = parse_float(row.get("DDm"))
            pdm = parse_float(row.get("PDm"))
            if ddm is not None:
                record.ddm = ddm
            if pdm is not None:
                record.pdm = pdm
            record.market_wacc_cost = parse_float(row.get("wacc_cost_of_debt,_(%)"))
            record.market_wacc_weight = parse_float(row.get("wacc_debt_weight,_(%)"))
            record.market_debt_total = parse_float(row.get("debt_total"))
            record.market_de_ratio = parse_float(row.get("d/e"))

    return records


def approx_zero(value: Optional[float], *, tol: float = 1e-6) -> bool:
    return value is not None and abs(value) <= tol


def in_zero_cost_group(record: Record, *, dataset: str) -> bool:
    if dataset == "accounting":
        return approx_zero(record.acct_wacc_cost) and approx_zero(record.acct_wacc_weight)
    return approx_zero(record.market_wacc_cost) and approx_zero(record.market_wacc_weight)


def in_low_debt_group(record: Record, *, dataset: str) -> bool:
    debt_total = record.acct_debt_total if dataset == "accounting" else record.market_debt_total
    return debt_total is not None and debt_total <= 1.0


def in_low_leverage_group(record: Record, *, dataset: str) -> bool:
    d_e = record.acct_de_ratio if dataset == "accounting" else record.market_de_ratio
    return d_e is not None and d_e <= 0.05


def get_dd(record: Record, *, dataset: str) -> Optional[float]:
    return record.dda if dataset == "accounting" else record.ddm


def is_outlier(record: Record, *, dataset: str) -> bool:
    dd_value = get_dd(record, dataset=dataset)
    return dd_value is not None and dd_value > OUTLIER_THRESHOLD


def get_debt_weight(record: Record, *, dataset: str) -> Optional[float]:
    return (
        record.acct_wacc_weight
        if dataset == "accounting"
        else record.market_wacc_weight
    )


def get_de_ratio(record: Record, *, dataset: str) -> Optional[float]:
    return (
        record.acct_de_ratio if dataset == "accounting" else record.market_de_ratio
    )


def dd_difference(
    record: Record, *, minuend: str, subtrahend: str
) -> Optional[float]:
    minuend_value = get_dd(record, dataset=minuend)
    subtrahend_value = get_dd(record, dataset=subtrahend)
    if minuend_value is None or subtrahend_value is None:
        return None
    return minuend_value - subtrahend_value


def format_dd(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


def format_pd(value: Optional[float]) -> str:
    if value is None:
        return "—"
    if value == 0:
        return "0"
    if value >= 0.01:
        return f"{value:.2f}"
    return f"{value:.2e}"


def format_flag(value: bool) -> str:
    return "✓" if value else ""


def format_number(value: Optional[float], *, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def render_table(
    rows: Iterable[Record],
    *,
    dataset: str,
    extra_column: Optional[Tuple[str, Callable[[Record], str]]] = None,
) -> List[str]:
    header_cells = [
        "Instrument",
        "Year",
        "DDa",
        "DDm",
        "PDa",
        "PDm",
        "Zero-Cost Debt",
        "Debt ≤ 1",
        "D/E ≤ 0.05",
    ]
    if extra_column is not None:
        header_cells.append(extra_column[0])
    divider_cells = ["---"] * len(header_cells)

    lines = [
        "| " + " | ".join(header_cells) + " |",
        "| " + " | ".join(divider_cells) + " |",
    ]

    for record in rows:
        zero_cost = format_flag(in_zero_cost_group(record, dataset=dataset))
        low_debt = format_flag(in_low_debt_group(record, dataset=dataset))
        low_leverage = format_flag(in_low_leverage_group(record, dataset=dataset))

        row_cells = [
            record.instrument,
            str(record.year),
            format_dd(record.dda),
            format_dd(record.ddm),
            format_pd(record.pda),
            format_pd(record.pdm),
            zero_cost,
            low_debt,
            low_leverage,
        ]

        if extra_column is not None:
            row_cells.append(extra_column[1](record))

        lines.append("| " + " | ".join(row_cells) + " |")

    return lines


def summarize_groups(
    *,
    zero_cost: Iterable[Record],
    low_debt: Iterable[Record],
    low_leverage: Iterable[Record],
    other: Iterable[Record],
) -> List[str]:
    zero_cost_list = list(zero_cost)
    low_debt_list = list(low_debt)
    low_leverage_list = list(low_leverage)
    other_list = list(other)
    total = (
        len(zero_cost_list)
        + len(low_debt_list)
        + len(low_leverage_list)
        + len(other_list)
    )

    return [
        f"* Total flagged outliers (>{OUTLIER_THRESHOLD:g}): **{total}**",
        f"* Zero-cost debt inputs: **{len(zero_cost_list)}**",
        f"* Recorded debt ≤ 1: **{len(low_debt_list)}**",
        f"* Debt-to-equity ratio ≤ 0.05: **{len(low_leverage_list)}**",
        f"* Additional review required: **{len(other_list)}**",
    ]


def partition_records(
    records: Iterable[Record], *, dataset: str
) -> Tuple[List[Record], List[Record], List[Record], List[Record]]:
    zero_cost: List[Record] = []
    low_debt: List[Record] = []
    low_leverage: List[Record] = []
    other: List[Record] = []

    for record in records:
        if in_zero_cost_group(record, dataset=dataset):
            zero_cost.append(record)
        elif in_low_debt_group(record, dataset=dataset):
            low_debt.append(record)
        elif in_low_leverage_group(record, dataset=dataset):
            low_leverage.append(record)
        else:
            other.append(record)

    return zero_cost, low_debt, low_leverage, other


def additional_review_groups(
    records: Iterable[Record], *, dataset: str
) -> List[Tuple[str, List[Record], Optional[Tuple[str, Callable[[Record], str]]]]]:
    remaining: List[Record] = list(records)
    groups: List[Tuple[str, List[Record], Optional[Tuple[str, Callable[[Record], str]]]]] = []
    counterpart = "market" if dataset == "accounting" else "accounting"

    def extract_group(
        title: str,
        predicate: Callable[[Record], bool],
        extra: Optional[Tuple[str, Callable[[Record], str]]] = None,
    ) -> None:
        nonlocal remaining
        matched: List[Record] = []
        keep: List[Record] = []
        for record in remaining:
            if predicate(record):
                matched.append(record)
            else:
                keep.append(record)
        if matched:
            matched.sort(key=lambda r: (r.instrument, r.year))
            groups.append((title, matched, extra))
        remaining = keep

    if dataset == "accounting":
        extract_group(
            "#### Missing Market DD",
            lambda record: get_dd(record, dataset=counterpart) is None,
        )
        extract_group(
            "#### Moderately Low Leverage (0.05 < D/E ≤ 0.10)",
            lambda record: (
                (ratio := get_de_ratio(record, dataset=dataset)) is not None
                and 0.05 < ratio <= 0.10
            ),
            (
                "D/E",
                lambda record: format_number(
                    get_de_ratio(record, dataset=dataset)
                ),
            ),
        )
        extract_group(
            "#### Thin Debt Mix (Weight ≤ 10%)",
            lambda record: (
                (weight := get_debt_weight(record, dataset=dataset)) is not None
                and weight <= 10.0
            ),
            (
                "Debt Weight (%)",
                lambda record: format_number(
                    get_debt_weight(record, dataset=dataset)
                ),
            ),
        )
        extract_group(
            "#### Both Models Elevated (DDm > 13)",
            lambda record: (
                (ddm := get_dd(record, dataset=counterpart)) is not None
                and ddm > OUTLIER_THRESHOLD
            ),
        )
        extract_group(
            "#### Accounting ≫ Market (Δ ≥ 10)",
            lambda record: (
                (ddm := get_dd(record, dataset=counterpart)) is not None
                and ddm <= OUTLIER_THRESHOLD
                and (
                    (delta := dd_difference(
                        record, minuend=dataset, subtrahend=counterpart
                    ))
                    is not None
                )
                and delta >= 10
            ),
            (
                "ΔDD (Acct - Market)",
                lambda record: format_number(
                    dd_difference(record, minuend=dataset, subtrahend=counterpart)
                ),
            ),
        )
        extract_group(
            "#### Accounting ≫ Market (Δ 5-10)",
            lambda record: (
                (ddm := get_dd(record, dataset=counterpart)) is not None
                and ddm <= OUTLIER_THRESHOLD
                and (
                    (delta := dd_difference(
                        record, minuend=dataset, subtrahend=counterpart
                    ))
                    is not None
                )
                and 5 <= delta < 10
            ),
            (
                "ΔDD (Acct - Market)",
                lambda record: format_number(
                    dd_difference(record, minuend=dataset, subtrahend=counterpart)
                ),
            ),
        )
        extract_group(
            "#### Accounting ≫ Market (Δ 2-5)",
            lambda record: (
                (ddm := get_dd(record, dataset=counterpart)) is not None
                and (
                    (delta := dd_difference(
                        record, minuend=dataset, subtrahend=counterpart
                    ))
                    is not None
                )
                and 2 <= delta < 5
            ),
            (
                "ΔDD (Acct - Market)",
                lambda record: format_number(
                    dd_difference(record, minuend=dataset, subtrahend=counterpart)
                ),
            ),
        )
    else:
        extract_group(
            "#### Missing Accounting DD",
            lambda record: get_dd(record, dataset=counterpart) is None,
        )
        extract_group(
            "#### Moderately Low Leverage (0.05 < D/E ≤ 0.10)",
            lambda record: (
                (ratio := get_de_ratio(record, dataset=dataset)) is not None
                and 0.05 < ratio <= 0.10
            ),
            (
                "D/E",
                lambda record: format_number(
                    get_de_ratio(record, dataset=dataset)
                ),
            ),
        )
        extract_group(
            "#### Thin Debt Mix (Weight ≤ 10%)",
            lambda record: (
                (weight := get_debt_weight(record, dataset=dataset)) is not None
                and weight <= 10.0
            ),
            (
                "Debt Weight (%)",
                lambda record: format_number(
                    get_debt_weight(record, dataset=dataset)
                ),
            ),
        )
        extract_group(
            "#### Accounting ≫ Market (Δ ≥ 10)",
            lambda record: (
                (delta := dd_difference(
                    record, minuend=counterpart, subtrahend=dataset
                ))
                is not None
                and delta >= 10
            ),
            (
                "ΔDD (Acct - Market)",
                lambda record: format_number(
                    dd_difference(record, minuend=counterpart, subtrahend=dataset)
                ),
            ),
        )
        extract_group(
            "#### Accounting ≫ Market (Δ 5-10)",
            lambda record: (
                (delta := dd_difference(
                    record, minuend=counterpart, subtrahend=dataset
                ))
                is not None
                and 5 <= delta < 10
            ),
            (
                "ΔDD (Acct - Market)",
                lambda record: format_number(
                    dd_difference(record, minuend=counterpart, subtrahend=dataset)
                ),
            ),
        )
        extract_group(
            "#### Accounting ≫ Market (Δ 2-5)",
            lambda record: (
                (delta := dd_difference(
                    record, minuend=counterpart, subtrahend=dataset
                ))
                is not None
                and 2 <= delta < 5
            ),
            (
                "ΔDD (Acct - Market)",
                lambda record: format_number(
                    dd_difference(record, minuend=counterpart, subtrahend=dataset)
                ),
            ),
        )

    if remaining:
        remaining.sort(key=lambda record: (record.instrument, record.year))
        groups.append(
            (
                "#### Still Needs Investigation",
                remaining,
                ("Notes", lambda _: "⚠"),
            )
        )

    return groups


def build_section(records: Iterable[Record], *, dataset: str) -> List[str]:
    relevant_records = [r for r in records if is_outlier(r, dataset=dataset)]
    relevant_records.sort(key=lambda r: (r.instrument, r.year))

    zero_cost, low_debt, low_leverage, other = partition_records(
        relevant_records, dataset=dataset
    )

    out: List[str] = []
    dataset_label = "Accounting" if dataset == "accounting" else "Market"

    out.append(f"## {dataset_label} DD Outliers")
    out.append("")

    out.extend(
        summarize_groups(
            zero_cost=zero_cost,
            low_debt=low_debt,
            low_leverage=low_leverage,
            other=other,
        )
    )
    out.append("")

    groups = [
        ("### Zero-Cost Debt Assumptions", zero_cost, None),
        ("### Recorded Debt ≤ 1", low_debt, None),
        ("### Debt-to-Equity Ratio ≤ 0.05", low_leverage, None),
    ]

    for heading, rows, extra in groups:
        if not rows:
            continue
        out.append(heading)
        out.append("")
        out.extend(
            render_table(
                rows,
                dataset=dataset,
                extra_column=extra,
            )
        )
        out.append("")

    out.append("### Additional Review Required")
    out.append("")
    subgroups = additional_review_groups(other, dataset=dataset)
    if not subgroups:
        out.append("_No additional review cases._")
        out.append("")
    else:
        for heading, rows, extra in subgroups:
            if not rows:
                continue
            out.append(heading)
            out.append("")
            out.extend(
                render_table(
                    rows,
                    dataset=dataset,
                    extra_column=extra,
                )
            )
            out.append("")

    return out


def main() -> None:
    records = load_records()
    all_records = list(records.values())

    lines: List[str] = [
        "# Distance-to-Default Outliers (>13)",
        "",
        "This document lists bank-year combinations with accounting (DDa) or market (DDm) distance-to-default scores above 13.",
        "Entries are grouped by the data issues most commonly linked to extreme scores: zero-cost debt assumptions, negligible recorded debt, or very low leverage.",
        "Any remaining outliers are surfaced separately for deeper review and clustered by cross-model spreads, thin debt mixes, or moderately low leverage before surfacing unresolved cases.",
        "",
        "A dash (—) indicates the paired metric was unavailable in the source data (for example, when the market solver reported `missing_input`).",
        "",
    ]

    lines.extend(build_section(all_records, dataset="accounting"))
    lines.extend(build_section(all_records, dataset="market"))

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
