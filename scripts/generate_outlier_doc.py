#!/usr/bin/env python3
"""Generate the docs/reference/outlier.md report from merged DD/PD inputs."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
ACCOUNTING_CSV = ROOT / "data" / "merged_inputs" / "dd_pd_accounting.csv"
MARKET_CSV = ROOT / "data" / "merged_inputs" / "dd_pd_market.csv"
OUTPUT_MD = ROOT / "docs" / "reference" / "outlier.md"


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


def render_table(rows: Iterable[Record], *, dataset: str) -> List[str]:
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

        lines.append("| " + " | ".join(row_cells) + " |")

    return lines


def summarize_groups(records: Iterable[Record], *, dataset: str) -> List[str]:
    rows = list(records)
    total = len(rows)
    zero_cost = sum(1 for r in rows if in_zero_cost_group(r, dataset=dataset))
    low_debt = sum(1 for r in rows if in_low_debt_group(r, dataset=dataset))
    low_leverage = sum(1 for r in rows if in_low_leverage_group(r, dataset=dataset))

    return [
        f"* Total outliers: **{total}**",
        f"* Zero-cost debt inputs: **{zero_cost}**",
        f"* Recorded debt ≤ 1: **{low_debt}**",
        f"* Debt-to-equity ratio ≤ 0.05: **{low_leverage}**",
    ]


def build_section(records: Iterable[Record], *, dataset: str) -> List[str]:
    out: List[str] = []
    dataset_label = "Accounting" if dataset == "accounting" else "Market"

    out.append(f"## {dataset_label} DD Outliers")
    out.append("")

    out.extend(summarize_groups(records, dataset=dataset))
    out.append("")

    sorted_rows = sorted(records, key=lambda r: (r.instrument, r.year))
    out.extend(render_table(sorted_rows, dataset=dataset))
    out.append("")

    return out


def main() -> None:
    records = load_records()
    accounting_outliers = [r for r in records.values() if r.dda is not None and r.dda > 13]
    market_outliers = [r for r in records.values() if r.ddm is not None and r.ddm > 13]

    accounting_outliers.sort(key=lambda r: (r.instrument, r.year))
    market_outliers.sort(key=lambda r: (r.instrument, r.year))

    lines: List[str] = [
        "# Distance-to-Default Outliers (>13)",
        "",
        "This document lists bank-year combinations with accounting (DDa) or market (DDm) distance-to-default scores above 13. Each table highlights why a case is considered an outlier—zero-cost debt assumptions, negligible recorded debt, or very low leverage—and reports both DDa/DDm and their associated probabilities of default (PDa/PDm)."
        "",
        "",
        "A dash (—) indicates the paired metric was unavailable in the source data (for example, when the market solver reported `missing_input`).",
        "",
    ]

    lines.extend(build_section(accounting_outliers, dataset="accounting"))
    lines.extend(build_section(market_outliers, dataset="market"))

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
