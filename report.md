# Convert debt_total to actual USD for consistent V/F calculation

```python
debt_total_usd = df['debt_total'] * 1_000_000

df['DDm'] = np.where(
    df['solver_status']=='no_debt',
    np.nan,
    (np.log(df['asset_value']/debt_total_usd)
     + (df['rf'] - 0.5 * df['asset_vol']**2) * T)
    / (df['asset_vol'] * np.sqrt(T))
)
df['PDm'] = np.where(
    df['solver_status']=='no_debt',
    np.nan,
    norm.cdf(-df['DDm'])
)
```

A negative DDm indicates that the asset value is very close to, or below, the debt level given the estimated volatility. In the merged results file, the row for **MFIN 2020** shows such a case with DDm ≈ -0.11 and PDm ≈ 54%:

```csv
MFIN,2020,...,113858850.0,1.529743669597971,...,298326795.01303774,0.7802757803396355,converged,-0.11129181953638051,0.5443075289137895
```
(see `dd_pd_market.csv` lines 1204–1209).

---

### Diagnostics for the MFIN 2020 Row

The following table lists every input used by the solver and the resulting parameters:

| Variable                  |      Value      | Notes                        |
|---------------------------|----------------:|------------------------------|
| Market cap (E)            |   113,858,850   | USD                          |
| Equity volatility (σ_E)   |        1.5297   | trailing 12‑month std dev    |
| Debt total (F)            | 241.052 million | F = 241,052,000 USD          |
| Risk‑free rate (rf)       |        0.0044   | 0.44%                        |
| Asset value (V)           |   298,326,795   | solver output                |
| Asset volatility (σ_V)    |        0.7803   | solver output                |
| ln(V/F)                   |        0.2132   | V/F ≈ 1.24                   |
| rf − 0.5 σ_V²             |      −0.3000    | volatility adjustment        |
| Numerator                 |      −0.0868    | ln(V/F) + rf − 0.5 σ_V²      |
| **DDm**                   |   **−0.1113**   | final distance to default    |
| **PDm**                   |   **0.5443**    | Φ(−DDm)                      |

The solver initializes with `V0 = E + F ≈ 354.9 million` and `σ_V0 = σ_E`. It converges to a lower asset value (about 56 million less than the initial guess) and roughly half the volatility. Because the final asset value is only ~24% above the debt level and the volatility term is large, the numerator of the DDm formula becomes negative, producing a negative DDm and a high PDm.

---

## Calculation of Equity Volatility

The notebook merges an annualized equity volatility series from `equity_volatility_by_year.csv`. The first lines of this file show how missing values occur when there are not enough returns:

```csv
symbol,year,equity_volatility,equity_volatility_note
SSB.N,2015,,number of return too low for equity vol
SSB.N,2016,0.22929139227718928,
```

These volatilities were computed from daily equity returns and then annualized, representing a **trailing 12‑month standard deviation of returns** for each symbol-year.

---

## Request for 24‑Month Volatility

A longer horizon volatility can be estimated by combining two consecutive years of daily returns. Without the raw return series, an approximation can be obtained by taking the root‑mean‑square of the two annual volatilities. For example, for MFIN over 2019–2020:

```python
σ_2019 = 0.6155
σ_2020 = 1.5297
σ_24m ≈ sqrt((σ_2019² + σ_2020²)/2) ≈ 1.17
```

This higher volatility would feed into the same DDm formula and likely yield an even lower DDm (higher PDm).

To compute exact 24‑month volatilities, one would gather two years of daily prices, compute log returns, take their standard deviation, and annualize the result before re‑running the Merton solver.
