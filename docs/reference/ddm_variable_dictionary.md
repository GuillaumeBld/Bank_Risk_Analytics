       # DDm Variable Dictionary

The Distance to Default metric (DDm) tells us how many "volatility-sized steps" separate a company's current asset value from
the level of debt that would mean default. Put differently, it measures the cushion a firm has before creditors would no longer
be repaid.

## Formula at a glance

In the market notebook, DDm is computed with the classic Merton distance-to-default equation:

$$
DDm = \frac{\ln\left(\tfrac{V}{F}\right) + (r_f - 0.5 \sigma_V^2) T}{\sigma_V \sqrt{T}}
$$

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
$$
E = V \,\Phi(d_1) - F \, e^{-r_f T} \,\Phi(d_2)
$$

2. **Equity volatility as leveraged asset volatility**

   ```
   sigma_E = \frac{V * N(d₁)}{E} * sigma_V
   ```
$$
\sigma_E = \frac{V \,\Phi(d_1)}{E}\(\sigma_V)
$$

   where the Black–Scholes style terms are

   ```
   d₁ = [ln(V / F) + (r_f + 0.5 * sigma_V^2) * T] / (sigma_V * √T)
   d₂ = d₁ - sigma_V * √T
   ```
$$
d_1 = \frac{\ln\left(\tfrac{V}{F}\right) + \left(r_f + 0.5\,\sigma_V^2\right)T}{\sigma_V \sqrt{T}}
$$
$$
d_2 = d_1 - \sigma_V \sqrt{T}
$$ 

   `N(·)` is the cumulative normal distribution. In words, these expressions say that shareholders behave like call option
   holders: their claim is worth the asset value multiplied by the probability that assets end up above debt, minus the present
   value of debt times the probability of paying it. The equity volatility relation simply scales asset volatility by the
   sensitivity of equity to changes in assets.

A larger DDm means a wider safety margin between assets and the debt hurdle; a value near zero means the firm sits right on the
edge of potential default.

### Variable dictionary (market-approach)

Every quantity that feeds the DDm calculation is summarised below so readers can trace the path from raw market data to the final metric.

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

### Variable dictionary (accounting-approach)

The accounting-approach notebook applies the same Merton logic but swaps in book values taken directly from financial statements. It still solves for the hidden asset value (`V`) and asset volatility (`sigma_V`), only now it anchors the scale in reported assets and debt.

With those ingredients the accounting workflow computes the distance to default as:

```
DDa = [ln(V / F) + (0 - 0.5 * sigma_V^2) * T] / (sigma_V * √T)
```

The barrier `F` remains the face value of debt expressed in dollars, and the denominator still turns the safety cushion into asset-volatility steps. As before, the probability of default follows as `PDa = Φ(-DDa)`.

The table below lists every column the accounting workflow touches while building DDa and PDa so readers can compare the two approaches line by line.

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

## Market (DDm) vs. Accounting (DDa): side-by-side view

The two distances to default share the same Merton foundation but answer different questions and implicitly adopt different
probability measures. The variable dictionary tables above (see the DDm entries for `market_cap`, `equity_vol`, `rf`, etc., and
the DDa entries for `total_assets`, `debt_total`, `rf`, etc.) highlight how each method selects inputs to support its chosen
view of the world:

* **What information do they trust, and what measure does that imply?**
  * **DDm** leans on *current* market sentiment. It matches the observed equity value (`market_cap`) and equity volatility
    (`equity_vol`) from the market dictionary and keeps the drift at `μ = r`, the risk-free rate supplied by `rf`. That choice
    mirrors the risk-neutral or **Q-measure** perspective described in [^prob-measures], where expected growth is set to the risk-free rate so
    that discounted expectations reproduce market prices.
  * **DDa** leans on *reported* balance-sheet figures. It anchors the scale in accounting data such as `total_assets` and
    `debt_total` from the accounting dictionary and deliberately sets `μ = 0`. This corresponds to the real-world or **P-measure**
    stance outlined in [^prob-measures], which focuses on actual default frequencies and avoids assuming asset growth beyond audited book
    values.
* **How is expected growth handled?**[^drift]
  * **DDm** applies the numerator `(r - 0.5 sigma_V^2) T` using the `rf` input documented in the DDm dictionary. Positive rates lift
    the cushion, consistent with markets pricing in some asset drift.
  * **DDa** applies `(0 - 0.5 sigma_V^2) T` on purpose. Even with the shared `rf` column feeding the solver, the accounting formula keeps expected growth at zero so book assets are not projected beyond today’s audited balance sheet.
* **When might one be preferred?**
  * **DDm** reacts quickly to new market data, making it useful for trading desks or market-implied risk monitoring.
  * **DDa** stays steadier for regulatory, planning, or credit analysis that emphasises audited statements and empirical default
    frequencies. Moody’s KMV-style implementations map DDa-style distances to observed default rates under the P measure.

Seen together, DDm captures the market’s forward-looking, risk-neutral view, while DDa provides a grounded real-world check based
on accounting data. Comparing the two helps flag situations where market anxiety diverges from balance-sheet strength.

## How the solver works (using SciPy)

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
* The DDm score itself can be read like a z-score, but keep the banking sample in mind. Using the 1,404 bank-year observations
  where the solver converged in `dd_pd_market.csv`, the distribution of DDm looks like this:

  | Statistic | Value | Interpretation |
  | --- | ---: | --- |
  | Count | 1,404 | Converged bank-year rows included in the summary. |
  | Minimum | -0.11 | Only a handful of points fall at or slightly below the debt hurdle. |
  | 10th percentile | 3.41 | The weakest decile still retains a cushion just above three volatility steps. |
  | 25th percentile | 4.97 | Lower-quartile banks hold a moderate buffer. |
  | Median | 7.05 | Half of the sample sits roughly seven volatility units above default. |
  | 75th percentile | 9.51 | Upper-quartile banks operate with a pronounced safety margin. |
  | 90th percentile | 12.91 | The top decile enjoys double-digit cushions. |
  | Maximum | 49.91 | A few outliers exhibit exceptionally high implied distance to default. |

  These figures imply practical interpretation buckets tailored to the observed data:

  * **Below ~3**: distressed territory. Assets ride close to or below the debt barrier, so default risk is acute.
  * **Between ~3 and 7**: core range. This band covers the 10th to 50th percentiles and reflects a typical regulatory buffer.
  * **Between ~7 and 13**: strong cushion. Scores in the median-to-90th percentile range indicate comfortable solvency.
  * **Above ~13**: outlier strength. Only the top decile reaches double digits; treat these as exceptionally well-capitalised
    cases.

Explaining these outcomes in standard deviation language helps non-specialists interpret the metric without needing option-pricing
jargon.

## Walkthrough example: 2019 DDm comparison for two US banks

To make the abstractions concrete, the step-by-step layout below walks through the 2019 DDm calculation for **Bank of America** and **JPMorgan Chase**. Every input appears in the DDm variable dictionary, so you can trace each number back to its plain-language definition.

### Step 1: Collect the dictionary inputs

| Dictionary entry | Bank of America (2019) | JPMorgan Chase (2019) | Notes |
| --- | --- | --- | --- |
| `market_cap` (`E`) | 265.3 billion USD | 387.4 billion USD | Market value of equity used inside the solver equations. |
| `equity_vol` (`sigma_E`) | 0.279 (annual) | 0.227 (annual) | Observed stock volatility the solver must match. |
| `debt_total` | 430,169 million USD | 516,093 million USD | Reported debt before unit conversion. |
| `rf` (`r_f`) | 0.0214 | 0.0214 | One-year risk-free rate feeding the risk-neutral drift. |
| `asset_value` (`V`) | 686.3 billion USD | 892.6 billion USD | Solver output representing total firm assets. |
| `asset_vol` (`sigma_V`) | 0.108 (annual) | 0.099 (annual) | Solver output representing asset volatility. |

### Step 2: Rebuild the solver equations

Before the notebook can report `asset_value` and `asset_vol`, the root finder must satisfy the Merton relationships for each bank:

```
E = V * N(d₁) - F * e^{-r_f T} * N(d₂)
sigma_E = (V * N(d₁) / E) * sigma_V
d₁ = [ln(V / F) + (r_f + 0.5 * sigma_V^2) * T] / (sigma_V * √T)
d₂ = d₁ - sigma_V * √T
```

The algorithm starts from the intuitive guesses `V₀ = E + F` and `sigma_{V,0} = sigma_E`, plugs each bank’s observed `E`, `sigma_E`, `F`, and `r_f` into the equations above, and then lets SciPy’s `root` function adjust `V` and `sigma_V` until both equations line up with the market data. Once the residuals fall below the tolerance, the solver stores the converged `asset_value` and `asset_vol` values listed in Step 1.

### Step 3: Convert book debt into the default barrier `F`

The dictionary reminds us that `debt_total` is reported in millions. Multiplying by 1,000,000 puts the default barrier on the same scale as the solver’s asset value:

* Bank of America: `F = 430,169 × 1,000,000 ≈ 4.30 × 10^11` USD (430.2 billion).
* JPMorgan Chase: `F = 516,093 × 1,000,000 ≈ 5.16 × 10^11` USD (516.1 billion).

### Step 4: Apply the DDm formula component by component

The distance-to-default formula combines leverage, drift, and volatility:

```
DDm = [ln(V / F) + (r_f - 0.5 * sigma_V^2) * T] / (sigma_V * √T)
```

Using `T = 1` year and the Q-measure drift `μ = r_f`, we can write out each piece for both banks. Values are rounded to three decimal places for readability.

| Bank | `ln(V / F)` | `(r_f - 0.5 sigma_V^2) * T` | Numerator | Denominator (`sigma_V √T`) | Resulting `DDm` |
| --- | --- | --- | --- | --- | --- |
| Bank of America | 0.467 | 0.016 | 0.483 | 0.108 | **4.48** |
| JPMorgan Chase | 0.548 | 0.017 | 0.564 | 0.099 | **5.73** |

Each numerator combines the leverage cushion `ln(V / F)` with the drift adjustment, and each denominator simply equals `sigma_V` because `√T = 1`.

### Step 5: Interpret the scores in everyday language

* **Bank of America (DDm ≈ 4.5):** Assets sit about four and a half volatility steps above the debt barrier. That is a comfortable buffer, though it leaves less room than JPMorgan once you account for the higher asset volatility.
* **JPMorgan Chase (DDm ≈ 5.7):** A larger leverage cushion and slightly calmer asset volatility combine to push the score above five standard deviations, signalling even lower near-term default risk under the market-based (Q-measure) view.

Walking through the example in this way shows how the dictionary entries plug directly into the solver outputs and the DDm formula, making it easier for non-specialist readers to replicate or sanity-check the calculation.

[^prob-measures]: **Risk-neutral measure (Q-measure).** Investors are assumed to demand only the risk-free rate after adjusting for risk, so assets drift at `r_f` and discounted expectations match market prices. **Real-world measure (P-measure).** Probabilities track actual economic frequencies, letting assets grow or shrink at the business’s realised rate instead of the risk-free rate.

[^drift]: Drift (`μ`) tunes the assumed asset growth in the distance-to-default formula `DD(μ) = [ln(V / F) + (μ - 0.5 * sigma_V^2) * T] / (sigma_V * √T)`. DDm evaluates the expression with `μ = r_f`, so rising rates widen the cushion, while DDa fixes `μ = 0` to keep book assets frozen at today’s audited level.
