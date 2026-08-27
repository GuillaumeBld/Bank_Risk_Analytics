# Audit: Distance-to-Default / Probability-of-Default pipeline
**Repository:** GuillaumeBld/Bank_Risk_Analytics (default branch, cloned 2026-08-26)
**Scope:** `dd_pd_market.ipynb`, `dd_pd_accounting.ipynb`, `merging.ipynb`, `analysis.ipynb`, `scripts/02_calculate_equity_volatility.py`, `utils/`, and the shipped outputs in `data/outputs/datasheet/`.
**Method:** static read of every computational cell, then independent re-computation from the raw inputs in `data/clean/` using a clean pandas/scipy environment. Every claim below is backed by a number reproduced outside the notebooks.

---

## Verdict

The **numerical machinery is correct**. The Merton solver genuinely converges, the volatility estimator genuinely has no lookahead, and the DD/PD formulas match the literature.

The **economic inputs are wrong**. The variable used as the default barrier `F` is not what the methodology document says it is, and one derived quantity in the accounting notebook is wrong under any convention. The result is that both DD series are inflated by roughly a factor of 2 to 10 and both PD series are numerically degenerate: 95% of `PD_a` and 60% of `PD_m` are below 1e-10. Any regression using PD as a dependent variable is estimating noise on a constant.

This is a data-column problem, not a code-rewrite problem.

---

## Finding 1 (critical). The default barrier `F` excludes deposits, contradicting the project's own written spec

**What the spec says.** `docs/writing/dd_and_pd.md`:
- line 14: "Barrier Convention: For banks, F = total liabilities (deposits are liabilities and dominate funding)."
- lines 383, 447: same statement repeated.
- line 480: "**Critical**: Book equity means total equity from balance sheet, **not** assets minus deposits or debt securities."

**What the code does.** Both notebooks set `F = debt_total * 1_000_000` with the inline comment "debt_total represents total liabilities (deposits dominate funding)".

**What the data says.** That comment is false.

| Check | Value |
|---|---|
| `debt_total / total_assets`, median | **0.060** |
| Implied book equity / assets (`market_cap / P-to-B / total_assets`), median | **0.109** |
| Implied true liabilities / assets, median | **0.891** |
| **`debt_total` as a share of true total liabilities, median** | **0.069** |

The implied equity/assets ratio of 10.9% is exactly what US bank capital ratios should look like, which confirms the back-out is sound. Against that benchmark, `debt_total` captures about **7% of the actual liability stack**. It is interest-bearing borrowings only. Deposits, the dominant funding source, are absent.

**Corroborating symptom in the shipped output.** In `market_20251011_042629.csv`:
- median `V/F` = **3.56** (real banks are near 1.10)
- median `E/F` = **2.57**, i.e. the model believes the median bank's market equity is 2.6 times its total debt
- max `V/F` = 107,897, a bank the model treats as essentially unlevered

No US bank has ever had that balance sheet. The Merton model is being asked to price a lightly levered industrial firm, not a bank.

**Affects:** `dd_pd_market.ipynb` cell 6, `dd_pd_accounting.ipynb` cell 8, and every downstream output.

---

## Finding 2 (critical, accounting notebook only). `be_usd` is not book equity

`dd_pd_accounting.ipynb` cell 8:

```python
df['be_usd'] = (df['total_assets'] - df['debt_total']) * MM
df['E_pb']   = df['price_to_book_value_per_share'] * df['be_usd']
```

Since `debt_total` is only 6% of assets, `be_usd` comes out at roughly **94% of total assets**. It is not book equity, it is assets minus a sliver of borrowings. This is the exact construction line 480 of the methodology document forbids, and it is wrong under **any** barrier convention, including one that deliberately excludes deposits. Book equity is an accounting identity, not a modelling choice.

Measured against the actual market cap file that is already in the repo:

| Quantity | Ratio to true market cap |
|---|---|
| `E_pb` (the proxy actually used, ~all rows) | median **8.50x**, p25 6.80x, p75 10.16x |

Worked example, JPM 2016: the notebook produces `E_pb` = **$2.69 trillion**. JPM's actual year-end 2016 market capitalization, from `data/clean/all_banks_marketcap_annual_2016_2023.csv`, is **$240 billion**. An 11-fold overstatement.

The market notebook does not have this problem: it uses the real market cap file, and its units are internally consistent (both legs in raw USD).

**Note:** the repo already contains the correct market equity for 99.9% of bank-years. The accounting notebook is using a broken proxy for a quantity it does not need to proxy.

---

## Finding 3 (critical, consequence). Both PD series are numerically degenerate

Final analysis file `esg_dd_pd_20251011_043202.csv`, n = 1,290:

| | median | share < 1e-10 | share < 1e-6 |
|---|---|---|---|
| `PD_a` | 6.25e-35 | **95%** | 98% |
| `PD_m` | 6.48e-13 | **60%** | 84% |

A dependent variable that is zero to 35 decimal places for 95% of the sample carries no cross-sectional information. Every `PD_a` and `PD_m` regression in `analysis.ipynb` (cells 35 and 39) is uninterpretable, and any reported null result on them is an artifact of the barrier, not evidence about ESG.

`DD_a` and `DD_m` correlate at 0.95, which reads as strong convergent validity but is largely mechanical: both are driven by the same understated `F`.

---

## Impact quantified

Independent re-computation from raw inputs. `F_correct` = total assets minus implied book equity; `E_correct` = the market cap file already in the repo.

**Bharath-Shumway naive DD** (n = 1,423):

| Specification | DD p10 | DD median | DD p90 | PD median | share PD > 1e-4 |
|---|---|---|---|---|---|
| As coded | 7.20 | **11.81** | 19.14 | 1.7e-32 | 0.6% |
| Fix E only | 2.79 | 5.69 | 10.81 | 6.5e-09 | 15.9% |
| Fix E and F | -0.76 | **1.28** | 3.19 | 1.0e-01 | 72.1% |

**Merton market DD**, full solver re-run on a 200-row random sample (max residual 8.7e-13, so the comparison is clean):

| Specification | DD_m p10 | DD_m median | DD_m p90 | sigma_V median | PD median | share PD > 1e-4 |
|---|---|---|---|---|---|---|
| As coded | 4.24 | **6.99** | 11.69 | 0.1793 | 1.4e-12 | 6.0% |
| F = total liabilities | 2.87 | **4.37** | 5.84 | **0.0396** | 6.3e-06 | 33.5% |

Two things to read here. First, the market approach is partially self-correcting: the solver absorbs some of the barrier error into `sigma_V`, so DD_m moves 6.99 to 4.37 rather than collapsing. Second, the corrected asset volatility of **3.96%** is the number that should convince you. Bank asset volatility in the literature sits in the 1% to 5% band. The pipeline currently reports 17.9%, which is an equity-like volatility, because the model does not know the bank is levered.

**Read the corrected columns as magnitude demonstrations, not as the corrected estimates.** They rest on liabilities implied through price-to-book, and naive-PD levels are known to be poorly calibrated in absolute terms even when correctly specified. What they establish is the size and direction of the error, not the replacement values.

---

## Finding 4 (high). 127 duplicated bank-years are resolved by arbitrary row selection

Duplicate `(instrument, year)` keys:

| File | rows | duplicate keys |
|---|---|---|
| `Book2_clean.csv` (input) | 1,426 | 1 |
| `equity_volatility_by_year.csv` (input) | 1,311 | 3 |
| `accounting_20251011_042604.csv` | 1,431 | 7 |
| `market_20251011_042629.csv` | 1,305 | 15 |
| `merged_20251011_043202.csv` | **1,551** | **127** |
| `esg_dd_pd_20251011_043202.csv` | 1,424 | 0 |

A handful of duplicate keys in two input files pass through a many-to-many volatility merge, then through `pd.merge(..., how='outer')` in `merging.ipynb` cell 4, and fan out into 127 duplicated bank-years and 127 extra rows. `merging.ipynb` cell 6 then collapses them with `drop_duplicates(keep='first')`.

For those 127 bank-years, which DD/PD value survives into the analysis file is decided by row order, not by any rule. It is silent and it is undocumented. The market notebook already contains a deliberate dedup step (cell 6, keep max `debt_total`); the volatility file and the merge have no equivalent.

---

## Finding 5 (medium). The time-integrity assertions are tautological

`dd_pd_market.ipynb` cell 12 and `dd_pd_accounting.ipynb` cell 10 assign:

```python
df['sigmaE_window_end_year'] = df['year'] - 1
```

Then cell 13 / cell 11 assert:

```python
assert (df['sigmaE_window_end_year'] == df['year'] - 1).all()
```

and `utils/time_checks.assert_time_integrity` re-checks the same identity. The assertion verifies a value the notebook itself just wrote one cell earlier. It would pass unchanged if the volatility file contained pure lookahead.

The good news: the real guarantee exists and is genuine. `scripts/02_calculate_equity_volatility.py` cuts at `pd.Timestamp(f'{target_year}-01-01')` and takes `.tail(36)` of strictly prior months. **There is no lookahead in sigma_E.** The point is that the assertion is not what proves it, so it cannot catch a regression. A real check would validate the window fields carried in the volatility file itself against `year`.

---

## Finding 6 (medium). Sample selection through the Tier 1 filter

`scripts/02_calculate_equity_volatility.py` step 4 restricts sigma_E to bank-years classified Tier 1 in `total_return_diagnostic.csv`. Roughly 8% of bank-years are dropped, and they are dropped precisely because their return history is thin or irregular. Thin, irregular return history correlates with small, illiquid, and distressed banks, which is the tail that matters most for a default study. The README frames this as "90.6% coverage"; it is more accurately a non-random exclusion and belongs in the limitations section with a comparison of dropped-versus-kept characteristics.

---

## Finding 7 (medium). Drift is inconsistent between the two measures

- Market: `mu = r_f`, the risk-neutral drift. `DD_m = d2`, which is the risk-neutral distance to default, and `PD_m` is therefore a risk-neutral probability.
- Accounting: `mu_hat = r_{i,t-1}`, the firm's own lagged equity return, following Bharath-Shumway. This is a physical-measure drift.

Both are individually defensible and both are documented. But `DD_a` and `DD_m` are then compared, regressed on each other (`analysis.ipynb` cell 14), instrumented against each other (cell 17), and used as substitute dependent variables, as though they measured the same object. They do not: one is a Q-measure quantity and one is a P-measure quantity. This is a caveat to state, not a bug to fix, but it should be stated.

---

## Finding 8 (low, but it breaks a cell). `size_dummy` in `analysis.ipynb`

Cell 12 builds `size_dummy` by median split. Cell 25 then overwrites it:

```python
df['size_dummy'] = (df['a_total_assets'] > 1.0).astype(int)
```

`total_assets` is denominated in millions, so `> 1.0` selects every bank with more than one million dollars of assets, that is, all of them. The dummy would be a constant. In practice the column `a_total_assets` does not exist in the current merged file (the merge prefixes it `m_total_assets`), so the cell raises `KeyError` instead. Either way, no size control is being applied from cell 25 onward.

Related, cell 19: `OUTLIER_THRESHOLD = 13.0` is a hard-coded absolute DD cut with no stated basis. It only looks reasonable because DD is inflated; on corrected values it would flag almost nothing.

---

## What I verified as correct

Stated plainly, because it means the fix is narrow:

1. **The Merton solver converges for real.** I recomputed both residuals independently from the shipped `asset_value` and `asset_vol` columns for all 1,305 converged rows. Relative price residual: median 3.1e-13, max 1.4e-08. Volatility residual: median 2.0e-11, max 1.8e-08. Zero rows fail the stated tolerances of 1e-6 and 1e-4. The 100% convergence claim is true. No parameter sits at a bound. `sigma_V < sigma_E` on all 1,305 rows, as it must be for a levered firm.
2. **The DD formulas are right.** `DD_m = d2 = [ln(V/F) + (r_f - 0.5 sigma_V^2)T] / (sigma_V sqrt(T))`. Correct. `DD_naive = [ln((E+F)/F) + (mu - 0.5 sigma_V^2)T] / (sigma_V sqrt(T))` with `sigma_D = 0.05 + 0.25 sigma_E` and value-weighted `sigma_V`. That is Bharath-Shumway (2008) exactly.
3. **sigma_E is correctly constructed.** Log returns, 36-month trailing standard deviation, annualized by sqrt(12), strict pre-January-1 cutoff. The EWMA fallback weights are correctly ordered so the most recent month gets the highest weight.
4. **The risk-free rate is handled correctly.** Fama-French annual `rf` is in percent and is divided by 100. 2016 gives 0.0020, which matches the realized one-month bill.
5. **Units are internally consistent in the market notebook.** Market cap is raw USD, `debt_total` is scaled by 1e6 to raw USD. The unit bug flagged in the cell 19 markdown was genuinely fixed. The remaining problem is which liability concept `debt_total` measures, not its scale.

---

## Recommended fix order

1. **Source true total liabilities** (or total shareholders' equity, then subtract) per bank-year and repoint `F` at it. I checked whether the repo can derive this from what it already has: `debt_total / (d/e)` does not reproduce implied book equity (ratio median 1.93, p25 1.19, p75 3.59, max 46,436). **The `d/e` column will not work.** This needs a real balance sheet pull: Refinitiv/Compustat total liabilities, or FR Y-9C schedule HC for the bank holding companies. This is the one item that requires new data.
2. **In `dd_pd_accounting.ipynb`, replace the `E_pb` / `E_de` / `E_wacc` proxy cascade with the actual market cap** from `all_banks_marketcap_annual_2016_2023.csv`, which covers 99.9% of bank-years. Keep the proxy cascade only as a fallback for the 0.1%, and keep `E_source` for provenance. This removes the 8.5x inflation immediately and does not need new data.
3. **Deduplicate on `(instrument, year)` with an explicit, logged rule before every merge**, and change `merging.ipynb` to `validate='1:1'` so a duplicate raises instead of fanning out.
4. **Re-run the full pipeline and re-examine PD.** If PD is still degenerate after the barrier fix, report DD only and say so, rather than regressing on a constant.
5. **Replace the tautological time assertions** with checks against the window fields carried in the volatility file.
6. **Fix `size_dummy`**, drop or re-derive `OUTLIER_THRESHOLD`, and add the Q-measure versus P-measure caveat to the methodology document.
7. **Update the README.** "100% convergence" and "90.6% coverage" are true but they measure solver health and row counts, not economic validity. Both were green while the barrier was off by 14x. A validity check belongs alongside them: median `V/F` in a plausible band for banks, and median `sigma_V` in the 1% to 5% band.

---

## One note outside this repo

`esg-bank-risk` almost certainly consumes these DD/PD series as its dependent variables. If so, its reported null result across 60 System GMM specifications is downstream of a dependent variable that is zero to 35 decimal places for most of the sample, and the paper's finding cannot be interpreted until the barrier is fixed and the series regenerated. I did not audit that repository; flagging it as a dependency, not as a conclusion.
