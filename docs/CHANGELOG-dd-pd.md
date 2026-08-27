# DD/PD dataset changelog

## 2026-08-27 — corrected default barrier (v4.0)

Supersedes the v3.0 datasheets in `data/outputs/datasheet/`. Those remain in the
repository as the historical record and must not be used for new analysis.

**What changed, and why the old numbers were wrong**

| | v3.0 | v4.0 |
|---|---|---|
| Default barrier `F` | `debt_total` (borrowings only) | total liabilities |
| Equity `E`, accounting model | `price_to_book * (assets - debt_total)` | observed market cap |
| Median `V/F` | 3.56 | **1.14** |
| Median `sigma_V` | 0.179 | **0.036** |
| Share of `PD_m` above 1e-6 | 16.2% | **63.8%** |
| Share of `PD_a` above 1e-6 | 1.4% | **98.6%** |

The v3.0 barrier captured a median 6.9% of the real liability stack, because
`debt_total` counts interest-bearing borrowings and excludes deposits. Bank asset
volatility belongs in the 1 to 5 percent band; v3.0 reported 17.9%, an
equity-like number, which is the signature of a barrier that hides the leverage.

**Barrier source**

`TR.F.TotLiab`, the published balance sheet line, pulled per bank-year through
Refinitiv. 1,893 bank-years for 239 of 244 banks. Of the panel's 1,422 resolved
rows, **1,389 take the reported line** and 33 fall back to the accounting
identity `total_assets - market_cap / price_to_book` where the vendor has no
usable row.

**Two identifier traps, both hit and both caught**

`List_bank.xlsx` carries a `PermId` column, and keying on it is wrong: the
column is misaligned with the ticker column for part of the file. LARK's listed
PermId returns KeyCorp; KEY's returns JPMorgan Chase. Keying on PermId gave a
90.7% asset-agreement rate. Keying on the `Symbol` column, which carries the
correct RIC including the `^` suffixes of the ten banks delisted in 2025-2026,
gives **99.6%**.

A vendor row is accepted only when two independent checks agree: the company
name returned by `TR.CommonName` shares a distinctive token with the panel's,
and the vendor's own total assets match the panel's to within 2%. The name check
alone caught `CIZN` resolving to a VictoryShares ETF. The asset check alone
caught the PermId misalignment. Neither catches both, which is why both run.
Per-ticker results are in `data/clean/ric_identity_check.csv`.

A wrong entity returns a complete, internally consistent balance sheet. No
plausibility band on the numbers can detect that; only an identity check can.

**Agreement between the two sources**

On the 1,313 bank-years where both exist, implied over reported has median
**1.000**, p25 0.984, p75 1.006. Against reported deposits plus debt, which
omits other liabilities and is therefore expected to sit slightly below, the
ratio is 0.9855 on 1,115 rows.

**Coverage**

1,422 of 1,424 bank-years carry a barrier. Merton converged on 1,304 of 1,304
attempted, and the two rows that drop out lack a usable equity volatility.

`DD_a` covers 1,082 rows rather than 1,422. Bharath-Shumway's drift is the
firm's own lagged return, so every bank loses its first panel year, 244 rows,
one per bank. Those are left undefined rather than filled from a peer group.

**Measure**

`DD_m` is risk-neutral (drift `r_f`); `DD_a` is physical (drift `r_{i,t-1}`).
`PD_m` and `PD_a` are therefore not comparable in level. Both are carried with a
`measure_m` / `measure_a` column so downstream code cannot lose track of it.

Closes #26, #27, #28, #29, #30, #31, #32.
