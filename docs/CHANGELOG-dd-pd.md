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

## 2026-08-27 — notebooks converted to callers

The four notebooks no longer compute anything. The model lives in `ddpd/`, and
each notebook now explains one part of it, calls it, and checks the result.

| Notebook | Was | Is |
|---|---|---|
| `dd_pd_market.ipynb` | 25 cells, two solver implementations inline | 18 cells: the Merton derivation, one firm solved end to end, panel diagnostics, the gate |
| `dd_pd_accounting.ipynb` | 21 cells, proxy cascade and imputation chain inline | 14 cells: the Bharath-Shumway proxies, one firm by hand checked against the module, coverage, the gate |
| `merging.ipynb` | outer-joined two DD/PD datasets, 127 duplicate keys | joins the single panel onto the ESG panel, `validate="1:1"`, gate before writing |
| `analysis.ipynb` | read the newest `merged_*.csv` by mtime | reads `esg_dd_pd_latest.csv`, a stable name written only after the gate passes |

The market notebook previously defined the solver **twice**, in cells 15 and 18,
with different bounds, tolerances and convergence criteria; cell 17 ran one and
cell 18 ran the other. There is now one implementation, in `ddpd/models.py`,
covered by `tests/test_models.py`.

Each notebook is committed with its outputs from a real execution against the
committed panel. All four run start to finish with zero errors.

**Also in this change**

- `size_dummy` in `analysis.ipynb` is a median split. It was `total_assets > 1.0`
  on a column denominated in millions, which selected every bank in the panel, so
  no size control was applied from that cell onward. Closes #33.
- A fifth acceptance band, median barrier over total assets, in [0.75, 0.97].
  It is the only band that inspects the input rather than the output: v3.0's
  `debt_total` gives 0.060 here and fails immediately, where every other band
  catches the defect only after it has passed through the solver. Suggested by a
  downstream consumer of these series.

## 2026-08-27 — corrected drift for the naive model (v4.1)

**`DD_a` and `PD_a` change again. `DD_m` and `PD_m` are unchanged**, because the
Merton drift is the risk-free rate and never touched `rit`.

### The defect

`Book2_clean.csv` carries a `rit` column, the annual equity return. It is the
drift of the Bharath-Shumway model, and `DD_a` correlates **0.96** with it, so
it drives the accounting series almost entirely.

It disagrees with two independent measures of the same quantity:

| Pair | Correlation |
|---|---|
| monthly-compounded vs change in market cap | **0.928** |
| `rit` vs monthly-compounded | 0.460 |
| `rit` vs change in market cap | 0.403 |

Two sources agree with each other and disagree with `rit`. That makes `rit` the
outlier, not the referee. JPMorgan returned about 47% in 2019: the monthly file
gives 0.4727, the market cap change 0.4280, `rit` gives 0.1831.

For Signature Bank `rit` is not merely wrong but **impossible**, reporting
**-424%** and **-238%** in consecutive years. A shareholder cannot lose more
than the position. Those two rows produced the worst `DD_a` values in the
shipped panel, -29.7 and -17.0. The v3.0 notebook printed a warning about `rit`
falling outside [-1, 1] and then used the value anyway; the first version of
this pipeline dropped even the warning.

### The fix

The drift is compounded from `raw_monthly_total_return_2013_2023 (1).csv`, the
same file `scripts/02_calculate_equity_volatility.py` already trusts to build
`sigma_E`. The volatility and the drift of one model now come from one source.

`ddpd/models.py` additionally rejects any drift outside [-0.99, 3.0] rather than
clipping it: an impossible return is a broken input, and clipping invents a
number for a bank-year that cannot be measured.

### Effect

| `DD_a` | v4.0 | v4.1 |
|---|---|---|
| rows | 1,082 | **1,286** |
| min | -29.73 | **-3.24** |
| skew | -2.13 | **0.59** |
| kurtosis | **71.34** | **0.59** |
| share of `PD_a` above 1e-6 | 98.7% | 91.1% |

Correlation with the v4.0 series is **0.499** (rank 0.709), so this is a second
material change rather than a rescaling.

Coverage rises because the monthly file starts in 2013, so a lagged drift exists
for 2016. The v4.0 note that every bank loses its first panel year no longer
holds: 1,336 rows take the compounded return, 54 fall back to a plausible `rit`
where the bank is absent from the monthly file, and 32 have no drift at all.

### How it was found

A downstream consumer reported that specifications on `DD_a` passing their
diagnostics fell from 15 to 3 against the v4.0 series, and offered the
explanation that the old degenerate variable had been passing specification
tests without measuring anything. That is partly true, but checking the tail
instead of accepting the flattering reading surfaced a drift of -424%.

## 2026-08-27 — gate hardened after an independent cross-family review (v4.2)

**No DD/PD value changes.** Every number in the panel is identical; this changes
what the gate refuses.

An independent review by DeepSeek, a different model family, was given the
module and its tests and asked to defeat the gate rather than approve it. It
did, by construction. The full review is in
`docs/review/2026-08-27_deepseek_independent_review.md`.

### What it broke, verified against the real code and data before fixing

| | Attack | Old verdict | Now |
|---|---|---|---|
| 1 | v3.0 barrier applied to **2023 only** | **PASS** | FAIL |
| 2 | v3.0 barrier applied to 2021-2023 | **PASS** | FAIL |
| 3 | run with no `--expected-rows` | **PASS** | BLOCKED |
| 4 | delete the `assets_usd` column | **PASS** | BLOCKED |
| 5 | delete the `sigma_E` column | **KeyError** | BLOCKED |
| 6 | drift never cross-checked | no check | FAIL |

The first is the one that mattered. Every band was a panel median, so a defect
confined to a minority of rows was diluted by the good rows: with 2023 priced on
the v3.0 barrier, that year sat at V/F 2.73 while the panel median stayed at
1.16 and the gate printed "PASS: every band holds". 2023 is the year US banks
failed, which is the worst place for a defect to hide.

The review also observed that four of the five bands were the same degree of
freedom, leverage, transformed four ways. That is why the medians diluted so
easily.

### The fixes

- **Per-year bands.** Median V/F and median sigma_V are now checked for every
  year as well as for the panel, with a wider tolerance because a year is a
  smaller sample. The per-year table is printed whether it passes or not.
- **Coverage is mandatory.** `--expected-rows` is required; without it the run
  is BLOCKED, not passed.
- **No check can be deleted by deleting a column.** `assets_usd` and `sigma_E`
  join the required set, so a missing column is a clean BLOCKED instead of a
  skipped band or a traceback.
- **The drift carries its own verification.** The agreement between the
  compounded drift and the year-on-year change in market cap is now a column on
  the panel and a thresholded band at 0.70, not a line in the log. The v3.0
  defect was an unverified drift; moving its source without thresholding the
  agreement would have left the same hole in a new place.
- **Year-exact fallback.** The `rit` fallback used `groupby.shift(1)`, a row
  shift, which is the previous year only when a bank's panel has no gap. It now
  merges on the year. No row in the current panel was affected; the mechanism
  was real and latent.
- **Rejected barriers are named.** The plausibility filter logged only a count.
  It now logs each rejected bank-year with its ratio and its source, because a
  silent filter on that band would remove the distressed tail that a
  default-risk panel exists to price. On this panel it rejects two rows,
  `HIFS` 2021 and 2022, and both are vendor errors rather than distress.
- **`_dedupe` no longer crashes** on a duplicated key whose rule column is
  entirely missing.

### One limit stated rather than papered over

A missing **first or last** year is not caught. Dropping 2023 leaves 81.4%
coverage and dropping 2016 leaves 87.1%, against a real panel at 91.6%: no floor
separates them without rejecting the real panel. A missing **interior** year is
caught by a contiguity check. The per-year table is where a reader sees an edge
year is absent. `test_a_missing_EDGE_year_is_a_known_limit_not_a_pass_to_be_faked`
pins this so a future change that tunes the floor to hide it will break.

### Two findings judged real but not live

- The `rit` fallback row-shift affects 0 of the 54 fallback rows in this panel.
- The solver can report success at its lower bound with a large residual for
  E/F below about 0.001; this panel stays above 0.02. The pipeline still records
  `converged` on `fit.success` alone. Left as is and recorded here.

### What the review confirmed

The finance is correct. It hand-checked and numerically round-tripped the Merton
and Bharath-Shumway implementations: no sign error, no wrong drift, `DD_m` is d2
and not d1, and the risk-neutral versus physical distinction is carried in the
output. It also judged the legacy-rejection test real and non-vacuous.

## 2026-08-27 — `rit` rebuilt at source, and a real Fama-French cost of equity (v5.0)

**`DD_m` and `DD_a` are unchanged**, both verified identical. This fixes the root
cause behind issue #35 instead of routing around it, and replaces the variable
that inherited it.

### `rit` rebuilt in the source files

The earlier fix rebuilt the drift inside the pipeline and left the broken column
in place, so every other consumer stayed exposed. `rit` is now rebuilt in
`Book2_clean.csv`, `esg_0718_clean.csv` and `esg_0718.csv` themselves, from the
monthly total returns.

| | legacy | rebuilt |
|---|---|---|
| minimum | **-4.2356** | -0.7520 |
| maximum | 2.7760 | 2.5957 |
| impossible values (below -100%) | 2 | **0** |
| rows moved by more than 10 points | | **795 of 1,361** |
| correlation legacy vs rebuilt | | **0.4598** |

Originals are kept as `rit_legacy` and `rit_rf_legacy`; nothing is deleted, so
anyone comparing old results to new can see exactly what moved. `rit_rf` is
recomputed as `rit - rf`, and `rit_source` records the provenance per row.

### A cost of equity that is one

`FF_Capital` is consumed by six scripts and computed by none. Regressing it on
the columns that do exist gives R-squared 0.95 with a dominant `rit_rf` term at
coefficient 0.73, so it is a shrunk transformation of the excess return. It
correlates **0.972** with `rit_rf` and only **0.63** with a correctly compounded
return, which is how it inherited the defect.

It is also not a cost of capital. Its values run from -42% to +44% with a median
of 3.9%. What shareholders require to hold a going concern cannot be negative.

`ddpd/factors.py` builds the textbook quantity instead:

```
cost_of_equity = rf_t + b_mkt*E[MKT] + b_smb*E[SMB] + b_hml*E[HML]
```

- Betas from OLS of the bank's monthly excess return on the three monthly
  factors, over a 60-month window ending December of t-1. Same no-lookahead rule
  as `sigma_E`, and at least 36 months or no estimate.
- Premia are long-run monthly means over 1926-2026, annualised: **MKT 8.34%,
  SMB 2.00%, HML 4.25%**. Using year t's realised factor return would produce a
  realised return, which is the error the legacy column embodies.
- Factors from Ken French's published file, committed as
  `data/clean/ff_factors_monthly_raw.csv`.

Result on the panel:

| | legacy `FF_Capital` | `ff_cost_of_equity` |
|---|---|---|
| median | 3.9% | **12.7%** |
| p10 to p90 | | 6.1% to 18.0% |
| negative values | ~25% of rows | **0** |

Betas are economically sensible for banks: market 0.73, HML **+0.89** (banks are
value stocks), SMB 0.85. The premia are recorded on every row, because they are
a modelling choice rather than a fact.

### One consequence worth stating

The pipeline's `rit` fallback for the drift is now **inert**. It existed to use
`rit` where the monthly file had no coverage; since `rit` is now built from that
same file, a missing month means both are missing. It costs 2 rows of `DD_a`
(1,286 to 1,284) and removes a path that read from a source documented as
unreliable. The fallback is kept for a `Book2` sourced elsewhere, and the log
now counts its uses so zero is visible rather than assumed.
