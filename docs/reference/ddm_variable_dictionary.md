# DDm Variable Dictionary

The Distance to Default metric (DDm) tells us how many "volatility-sized steps" separate a company's current asset value from
the level of debt that would mean default. Put differently, it measures the cushion a firm has before creditors would no longer
be repaid.

## Formula at a glance

In the market notebook, DDm is computed with the classic Merton distance-to-default equation:

```
DDm = [ln(V / F) + (r_f - 0.5 * sigma_V^2) * T] / (sigma_V * √T)
```

Where each symbol means:

* `ln(V / F)`: the natural logarithm of asset value divided by debt value. It captures the leverage of the firm in smooth,
  continuous terms.
* `(r_f - 0.5 * sigma_V^2) * T`: the expected drift in asset value over the horizon `T`, adjusted for risk. It reflects how assets
  tend to grow (or shrink) over time once we account for volatility.
* `sigma_V * √T`: the typical size of asset value swings over the same horizon. Dividing by this term translates the cushion into a
  number of standard deviations.

To place the formula in context, the default barrier `F` is the debt due at the horizon and the solver-provided `V` and `sigma_V`
represent the firm's current assets and how much they typically wiggle over time.

## Supporting equations from the Merton model

The DDm calculation depends on two option-style relationships that link the hidden asset inputs to the stock market data. They
are the targets that the solver tries to satisfy:

1. **Equity value as a call option on assets**

   ```
   E = V * N(d₁) - F * e^{-r_f T} * N(d₂)
   ```

2. **Equity volatility as leveraged asset volatility**

   ```
   sigma_E = \frac{V * N(d₁)}{E} * sigma_V
   ```

   where the Black–Scholes style terms are

   ```
   d₁ = [ln(V / F) + (r_f + 0.5 * sigma_V^2) * T] / (sigma_V * √T)
   d₂ = d₁ - sigma_V * √T
   ```

   `N(·)` is the cumulative normal distribution. In words, these expressions say that shareholders behave like call option
   holders: their claim is worth the asset value multiplied by the probability that assets end up above debt, minus the present
   value of debt times the probability of paying it. The equity volatility relation simply scales asset volatility by the
   sensitivity of equity to changes in assets.

A larger DDm means a wider safety margin between assets and the debt hurdle; a value near zero means the firm sits right on the
edge of potential default.

## How the solver works (plain-language walkthrough)

The notebook relies on a Merton-model root finder to uncover two hidden inputs—firm asset value (`V`) and asset volatility (`sigma_V`).
Those quantities are not directly observable, so the solver recovers them from market data using the following steps:

1. **Collect the known numbers.** For every firm-year observation we gather the stock market value (`market_cap`), the stock's
   historical volatility (`equity_vol`), the amount of debt outstanding (`debt_total`, converted to dollars), and the prevailing
   risk-free interest rate (`rf`). If any of these are missing, non-positive, or the firm reports zero debt, the solver stops and
   records the status so we do not compute an unreliable DDm.
2. **Translate the problem into two equations.** In the Merton framework, stockholders hold an option on the firm's assets. The
   solver therefore sets up two Black–Scholes style equations: one that should reproduce the observed equity value and another
   that should match the observed equity volatility. The explicit formulas are the ones shown above for `E` and `sigma_E`, and the
   unknowns in both equations are the true asset value `V` and its volatility `sigma_V`.
3. **Pick sensible starting guesses.** Numerical solvers need starting points. Here we begin with:
   * `V₀ = E + F`, the sum of observed equity value (`E`) and the face value of debt (`F`). This ensures the first guess at least
     equals the money already invested by shareholders and lenders.
   * `sigma_{V,0} = sigma_E`, the observed equity volatility. Using the market's own volatility keeps the guess within a believable range
     so the solver does not wander into unrealistic values.
4. **Let the root finder iterate.** The algorithm (SciPy's `root` with the hybrid method) plugs the guesses into the equations,
   measures how far the implied equity value and volatility differ from what we see in the data, and nudges the guesses toward a
   better fit. This compare-and-adjust loop repeats until both mismatches are effectively zero or the algorithm exhausts its
   iteration budget.
5. **Record the outcome.** If the differences shrink below the tolerance, the solver returns the fitted `V` and `sigma_V` and labels
   the row as `converged`. Otherwise it outputs `NaN` values and a descriptive status such as `no_debt` or `no_converge`. Only
   rows marked `converged` proceed to the DDm formula above.

### Why the initial guesses matter

The solver behaves like a person trying to balance two dials at once: one dial controls the asset value and the other dial controls
the asset volatility. If we start from a wild position, the algorithm may spin the dials for a long time or get stuck. Beginning
with `V₀ = E + F` and `sigma_{V,0} = sigma_E` gives the solver a head start because:

* The first guess for assets never falls below the money already committed by investors. That keeps the leverage ratio `V / F`
  realistic from the first iteration.
* Matching the asset volatility guess to the observed equity volatility acknowledges that equity usually wiggles more than assets,
  but not by orders of magnitude. The solver only needs to fine-tune that relationship instead of rescuing an extreme initial
  guess.

These grounded guesses help the root finder converge faster and lower the risk that it mislabels a solvable case as `no_converge`.

### Interpreting the outputs

Once the solver converges, the notebook adds two new columns and reuses existing ones:

* `asset_value` (`V`) and `asset_vol` (`sigma_V`) supply the hidden inputs that feed the DDm equation.
* `solver_status` acts as a quick quality check. Any value other than `converged` signals that the DDm should be treated as
  missing.
* The DDm score itself can be read like a z-score:
  * **Above 3**: assets sit several volatility steps above the debt hurdle—very low near-term default risk.
  * **Around 1 to 2**: the firm has a cushion, but it is not huge; watch for weakening fundamentals.
  * **Near 0 or negative**: assets hover at or below the debt level; default risk is high.

Explaining these outcomes in standard deviation language helps non-specialists interpret the metric without needing option-pricing
jargon.

## Variable dictionary (common-language version)

Every quantity that feeds the DDm calculation is summarised below. The table is grouped by where the variable comes from so that
non-specialist readers can trace the path from raw data to the final metric.

| Variable | Plain-language meaning | Where it comes from / units | Why it matters for DDm |
| --- | --- | --- | --- |
| `market_cap` (`E`) | Dollar value of all outstanding shares. | Observed market data, measured in USD. | Forms part of the solver equations and the starting guess `V₀ = E + F`.
| `equity_vol` (`sigma_E`) | How wildly the stock price moves from year to year. | Calculated from market returns, expressed as annual volatility (decimal). | Must be matched by the solver and seeds the initial guess `sigma_{V,0} = sigma_E`.
| `debt_total` | Reported debt amount before unit conversion. | Financial statements, expressed in millions of USD. | Converted to dollars so we can line up equity and debt in the same scale.
| `debt_total_usd` (`F`) | Debt level expressed in plain USD. | `debt_total * 1,000,000`. | Acts as the default barrier `F` inside `ln(V / F)` and the starting guess for total firm value.
| `rf` (`r_f`) | Risk-free interest rate over the year. | Fama–French data, stored as a decimal rate. | Supplies the drift term `(r_f - 0.5 sigma_V^2) * T` in the DDm numerator.
| `T` | Time window for the analysis. | Fixed to one year (`1.0`). | Scales both the expected drift and the volatility denominator `sigma_V √T`.
| `asset_value` (`V`) | Best estimate of the firm's total asset value today. | Output of the Merton solver, in USD. | Sits inside the leverage term `ln(V / F)` and shapes the size of the safety cushion.
| `asset_vol` (`sigma_V`) | Estimated volatility of the firm's assets. | Output of the Merton solver, annual volatility (decimal). | Appears in both the drift adjustment and the denominator of the DDm formula.
| `solver_status` | Diagnostic label indicating whether the solver succeeded. | Emitted by the numerical routine (e.g., `converged`, `no_debt`). | Only rows marked `converged` are used to compute DDm; other rows receive `NaN`.
| `DDm` | Final distance-to-default score. | Calculated result, measured in standard deviations. | The end product: how many volatility units separate assets from the debt hurdle.

## Accounting-based DDa at a glance

The companion accounting notebook applies the same logic but swaps in book values taken directly from financial statements. The solver still hunts for the pair of asset value (`V`) and asset volatility (`sigma_V`) that reconciles two Merton equations, only now it starts from balance-sheet data rather than equity market quotes:

* **Book equity as assets minus liabilities.** Observed equity becomes `E = total_assets - debt_total` after converting both figures from millions to actual dollars, so the solver works on the same scale as the accounts.
* **Shared risk-free series merged explicitly.** Both notebooks now pull the annual Fama–French `rf` column, convert it from percent to decimal once, and pass that shared series into the Merton equations. The accounting dataset still retains `rit` and `rit_rf` for diagnostics, but the solver discounts debt with the dedicated `rf` field while the final DDa step keeps the drift at zero to stay conservative about future asset growth.
* **Initial guesses anchored in the balance sheet.** The solver begins with `V₀ = total_assets` (in dollars) and `sigma_{V,0} = equity_vol`, so the first iteration honours the scale and variability implied by the accounting records.

With those ingredients the accounting notebook computes the distance to default as:

```
DDa = [ln(V / F) + (0 - 0.5 * sigma_V^2) * T] / (sigma_V * √T)
```

The barrier `F` remains the face value of debt expressed in dollars, and the denominator still turns the safety cushion into asset-volatility steps. As before, the probability of default follows as `PDa = Φ(-DDa)`.

### Variable dictionary (accounting version)

The table below lists every column the accounting workflow touches while building DDa and PDa. It mirrors the market-based dictionary so readers can compare the two approaches line by line.

| Variable | Plain-language meaning | Where it comes from / units | Why it matters for DDa |
| --- | --- | --- | --- |
| `total_assets` | Book value of the bank’s assets before unit conversion. | Financial statements, reported in millions of USD. | Seeds the solver’s starting asset guess and produces book equity (`E = assets - debt`). |
| `debt_total` | Book value of total debt before unit conversion. | Financial statements, reported in millions of USD. | Converted to dollars to provide the default barrier `F` inside `ln(V / F)`. |
| `equity_vol` (`sigma_E`) | Historical volatility of the bank’s equity returns. | Merged market data, annualised as a decimal. | Guides the solver and supplies the initial asset-volatility guess `sigma_{V,0}`. |
| `rf` (`r_f`) | Shared risk-free rate used by both notebooks. | Fama–French annual factors, stored as a decimal after dividing by 100. | Keeps the accounting solver’s discounting step consistent with the market workflow before the drift is set to zero. |
| `rit_rf` | Equity excess return (`R_it - R_f`). | Accounting dataset, decimal return. | Retained for audits—compare against `rit` and the merged `rf` to ensure the inputs line up. |
| `rit` | Observed equity return for the bank. | Accounting dataset, decimal return. | Paired with `rit_rf` to validate the merged `rf` series and to analyse realised performance. |
| `asset_value` (`V`) | Estimated total asset value consistent with the accounts. | Output of the accounting solver, in USD. | Feeds the leverage term `ln(V / F)` and underpins the DDa numerator. |
| `asset_vol` (`sigma_V`) | Estimated volatility of total assets. | Output of the accounting solver, annual volatility (decimal). | Appears in both the drift adjustment and the denominator `sigma_V √T`. |
| `dd_pd_tag` | Contextual flag explaining why DDa might be missing. | Emitted by the solver (e.g., `no_debt`, `negative_equity`). | When set, DDa and PDa are replaced with `NaN` so unreliable cases are excluded. |
| `merton_status` | Convergence indicator for the accounting solver. | Returned by SciPy’s root finder (`converged`, `no_converge`, etc.). | Confirms whether a valid `(V, sigma_V)` pair was found before computing DDa. |
| `DDa` | Accounting-based distance-to-default score. | Calculated result, in standard deviations. | Shows how many volatility units book assets sit above the book-debt hurdle. |
| `PDa` | Accounting-based probability of default. | Calculated result, as a probability between 0 and 1. | Converts the DDa cushion into a default likelihood via the normal CDF. |

## Probability-measure language in plain words

Before comparing the two distances to default, it helps to decode the two probability measures that appear in the literature:

* **Risk-neutral measure ("Q-measure").** Under this mathematical lens, we imagine investors are perfectly diversified and only
  demand the risk-free rate of return after adjusting for risk. Asset values are therefore expected to drift at the risk-free
  rate `r`, which makes it convenient to price securities because discounted expectations line up with market prices.
* **Real-world measure ("P-measure").** This perspective tracks the actual frequencies observed in the economy. Asset values are
  free to grow or shrink at whatever rate the business truly experiences, and the resulting probabilities line up with historical
  default counts.

Keeping those meanings in mind prevents confusion when the same formula is evaluated with different drift assumptions.

## Risk-free data sources and consistency checks

Both notebooks merge the dedicated Fama–French file (`fama_french_factors_annual_clean.csv`) that already contains the annual Treasury-bill return as the column `rf` (in percentage terms). Each workflow divides that series by 100 exactly once and reuses the resulting decimal wherever the Merton equations need a discount rate. Because the Fama–French feed is independent of any single bank, it gives a consistent economy-wide baseline for all instruments in a given year.

The accounting dataset still provides the realised return `rit` and the excess return `rit_rf = rit - rf`, but those columns now serve mainly as diagnostics: they let us verify that the merged `rf` aligns with the raw inputs and investigate realised performance under the P-measure. The solver itself discounts debt with the shared `rf` column before setting the drift to zero in the final DDa step.

Keeping both notebooks on the same risk-free series eliminates the earlier sign mistakes, preserves comparability between DDm and DDa, and honours the P-measure interpretation by only zeroing the drift **after** the solver has produced sensible `V` and `sigma_V` estimates.

## Market (DDm) vs. Accounting (DDa): side-by-side view

The two distances to default share the same Merton foundation but answer different questions and implicitly adopt different
probability measures. The variable dictionary tables above (see the DDm entries for `market_cap`, `equity_vol`, `rf`, etc., and
the DDa entries for `total_assets`, `debt_total`, `rf`, etc.) highlight how each method selects inputs to support its chosen
view of the world:

* **What information do they trust, and what measure does that imply?**
  * **DDm** leans on *current* market sentiment. It matches the observed equity value (`market_cap`) and equity volatility
    (`equity_vol`) from the market dictionary and keeps the drift at `μ = r`, the risk-free rate supplied by `rf`. That choice
    mirrors the risk-neutral or **Q-measure** perspective described above, where expected growth is set to the risk-free rate so
    that discounted expectations reproduce market prices.
  * **DDa** leans on *reported* balance-sheet figures. It anchors the scale in accounting data such as `total_assets` and
    `debt_total` from the accounting dictionary and deliberately sets `μ = 0`. This corresponds to the real-world or **P-measure**
    stance described above, which focuses on actual default frequencies and avoids assuming asset growth beyond audited book
    values.
* **How is expected growth handled?**
  * **DDm** applies the numerator `(r - 0.5 sigma_V^2) T` using the `rf` input documented in the DDm dictionary. Positive rates lift
    the cushion, consistent with markets pricing in some asset drift.
  * **DDa** applies `(0 - 0.5 sigma_V^2) T` on purpose. Even with the shared `rf` column feeding the solver, the accounting formula keeps expected growth at zero so book assets are not projected beyond today’s audited balance sheet.
* **When might one be preferred?**
  * **DDm** reacts quickly to new market data, making it useful for trading desks or market-implied risk monitoring.
  * **DDa** stays steadier for regulatory, planning, or credit analysis that emphasises audited statements and empirical default
    frequencies. Moody’s KMV-style implementations map DDa-style distances to observed default rates under the P measure.

Seen together, DDm captures the market’s forward-looking, risk-neutral view, while DDa provides a grounded real-world check based
on accounting data. Comparing the two helps flag situations where market anxiety diverges from balance-sheet strength.

### Drift sensitivity at a glance

**Drift (`μ`) describes the growth we allow assets to have during the one-year horizon.** Plugging a larger `μ` into the distance-to-default formula stretches the cushion; choosing a smaller one shrinks it.

```
DD(μ) = [ln(V / F) + (μ - 0.5 * sigma_V^2) * T] / (sigma_V * √T)
```

The table below spells out—in everyday language—what happens when we flip the drift between the two documented choices. The numerator column shows which inputs from the DDm and DDa dictionaries stay in play, and the final column summarises the human takeaway.

| Scenario | Measure style | Drift choice `μ` | Numerator impact | Plain-English takeaway |
| --- | --- | --- | --- | --- |
| `DDm` | Risk-neutral (**Q-measure**) | `μ = r` (uses the `rf` rate listed in the DDm dictionary) | `ln(V / F) + (r - 0.5 sigma_V^2) T` | Markets price assets as if they grow at the risk-free rate, so rising rates lift the DDm cushion. |
| `DDa` | Real-world (**P-measure**) | `μ = 0` (drift set to zero after solving with the shared `rf` column) | `ln(V / F) + (0 - 0.5 sigma_V^2) T` | Book-based analysis freezes asset growth, making the cushion smaller but safer. |

You can test other `μ` values by reusing the same formula—just swap in a different growth assumption and watch how the numerator changes. Keeping the labels clear (“DDm, market-based, Q-measure, `μ = r`; DDa, accounting-based, P-measure, `μ = 0`”) avoids mixing the two interpretations when comparing scores.

## Worked example: 2019 DDm comparison for two US banks

To make the abstractions concrete, the table-driven steps below walk through the 2019 DDm calculation for **Bank of America** and
**JPMorgan Chase**. Every input appears in the DDm variable dictionary above, so you can trace each number back to its plain-language
definition.

### Step 1: Collect the dictionary inputs

| Dictionary entry | Bank of America (2019) | JPMorgan Chase (2019) | Notes |
| --- | --- | --- | --- |
| `market_cap` (`E`) | 265.3 billion USD | 387.4 billion USD | Market value of equity used inside the solver equations. |
| `equity_vol` (`sigma_E`) | 0.279 (annual) | 0.227 (annual) | Observed stock volatility the solver must match. |
| `debt_total` | 430,169 million USD | 516,093 million USD | Reported debt before unit conversion. |
| `rf` (`r_f`) | 0.0214 | 0.0214 | One-year risk-free rate feeding the risk-neutral drift. |
| `asset_value` (`V`) | 686.3 billion USD | 892.6 billion USD | Solver output representing total firm assets. |
| `asset_vol` (`sigma_V`) | 0.108 (annual) | 0.099 (annual) | Solver output representing asset volatility. |

### Step 2: Convert book debt into the default barrier `F`

The dictionary reminds us that `debt_total` is reported in millions. Multiplying by 1,000,000 puts the default barrier on the same
scale as the solver’s asset value:

* Bank of America: `F = 430,169 × 1,000,000 ≈ 4.30 × 10^11` USD (430.2 billion).
* JPMorgan Chase: `F = 516,093 × 1,000,000 ≈ 5.16 × 10^11` USD (516.1 billion).

### Step 3: Apply the DDm formula component by component

Using `T = 1` year and the Q-measure drift `μ = r`, we can write out each piece of the DD equation for both banks. Values are
rounded to three decimal places for readability.

| Bank | `ln(V / F)` | `(r - 0.5 sigma_V^2) * T` | Numerator | Denominator (`sigma_V √T`) | Resulting `DDm` |
| --- | --- | --- | --- | --- | --- |
| Bank of America | 0.467 | 0.016 | 0.483 | 0.108 | **4.48** |
| JPMorgan Chase | 0.548 | 0.017 | 0.564 | 0.099 | **5.73** |

Each numerator combines the leverage cushion `ln(V / F)` with the drift adjustment, and each denominator simply equals `sigma_V` because
`√T = 1`.

### Step 4: Interpret the scores in everyday language

* **Bank of America (DDm ≈ 4.5):** Assets sit about four and a half volatility steps above the debt barrier. That is a
  comfortable buffer, though it leaves less room than JPMorgan once you account for the higher asset volatility.
* **JPMorgan Chase (DDm ≈ 5.7):** A larger leverage cushion and slightly calmer asset volatility combine to push the score
  above five standard deviations, signalling even lower near-term default risk under the market-based (Q-measure) view.

### Walking through the example in this way shows how the dictionary entries plug directly into the solver outputs and the DDm
formula, making it easier for non-specialist readers to replicate or sanity-check the calculation.
=======
The table below summarizes every variable that participates in the Distance to Default (DDm) calculation implemented in `dd_pd_market.ipynb`.

| Variable | Description | Units / Source | Role in DDm computation |
| --- | --- | --- | --- |
| `T` | Time horizon over which default risk is evaluated. | Years (set to 1.0). | Scales both the drift term and volatility denominator in the DDm formula. |
| `asset_value` (`V`) | Firm asset value estimated by the Merton solver for each instrument-year observation. | USD (solved from equity market cap, equity volatility, debt). | Appears in the log leverage term `ln(V/F)` and influences the drift component. |
| `asset_vol` (`σ_V`) | Asset volatility returned by the Merton solver. | Annualized volatility (decimal). | Used in both the drift adjustment `(r_f - 0.5 σ_V^2)T` and the denominator `σ_V √T`. |
| `debt_total` | Total debt from source data reported in millions of USD. | Millions of USD (raw input). | Converted to actual USD before forming the leverage ratio. |
| `debt_total_usd` (`F`) | Debt converted from millions to actual USD for consistent leverage calculations. | USD (`debt_total * 1,000,000`). | Serves as the default barrier `F` inside `ln(V/F)`. |
| `rf` (`r_f`) | Annual risk-free rate merged from Fama-French data and converted from percent to decimal. | Decimal rate. | Provides the drift term `(r_f - 0.5 σ_V^2)T` in the numerator. |
| `solver_status` | Flag emitted by the Merton solver indicating solution quality (`converged`, `no_debt`, etc.). | Categorical status. | Rows flagged `no_debt` skip DDm computation and receive `NaN`. |
| `DDm` | Distance to Default metric computed per observation. | Standard deviations. | Result of combining the above inputs via the Merton formula. |

