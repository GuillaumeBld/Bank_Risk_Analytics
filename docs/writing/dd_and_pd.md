# Understanding Distance to Default (DD) and Probability of Default (PD)

## Symbol Definitions (Used Throughout)

**Core Symbols** (no hats except in naive section):
- **V** = Firm asset value (USD)
- **F** = Face value of debt (USD)
- **σ_V** = Asset volatility (annual, decimal)
- **σ_E** = Equity volatility (annual, decimal)
- **r_f** = Risk-free rate (annual, decimal)
- **T** = Time horizon (years, typically 1)
- **Φ** = Standard normal cumulative distribution function

**Barrier Convention**: For banks, F = total liabilities (deposits are liabilities and dominate funding).

**Units Convention**: Millions converted to dollars once, not twice.

## ⏰ Time Index Conventions

**Critical**: All variables are indexed by time to prevent lookahead bias.

- **E_t**: Market capitalization observed during year t
- **F_t**: Barrier at t (for banks: total liabilities at t)
- **r_{f,t}**: One-year risk-free rate observed at t
- **σ_{E,t-1}**: Equity volatility computed only from returns up to t-1 (no future data)
- **μ̂_t**: For naive approach, equals r_{i,t-1} (previous year's equity return)
- **V_t, σ_{V,t}**: Solved at time t using only information available at t
- **T**: Time horizon = 1 year (from t to t+1)

**Key Statements**:
- DD_{m,t} equals d₂ when μ = r_{f,t} (Q-measure)
- DD_{naive,t} uses μ̂_t = r_{i,t-1} and is a P-style score unless calibrated
- **No lookahead**: σ_{E,t-1} window ends strictly at t-1

---

## Table of Contents
1. [Introduction](#introduction)
2. [What is Distance to Default?](#what-is-distance-to-default)
3. [What is Probability of Default?](#what-is-probability-of-default)
4. [The Merton Model Foundation](#the-merton-model-foundation)
5. [Market-Based Approach](#market-based-approach)
6. [Accounting-Based Approach](#accounting-based-approach)
7. [Comparing Both Approaches](#comparing-both-approaches)
8. [Data Quality: Trimming and Exclusions](#data-quality-trimming-and-exclusions)
9. [Results Interpretation](#results-interpretation)
10. [Walkthrough Examples](#walkthrough-examples)
11. [Appendix: Why d₂ is the z-score](#appendix)

---

## Introduction

This document explains how we measure the financial health and default risk of banking institutions using two complementary metrics: **Distance to Default (DD)** and **Probability of Default (PD)**.

### What You'll Learn

In simple terms:
- **DD (Distance to Default)**: How many "volatility steps" separate a bank's assets from its debt
- **PD (Probability of Default)**: The percentage chance of default within one year
- **Two Methods**: Market-based (using stock prices) vs Accounting-based (using balance sheets)
- **Data Quality**: How we handle unusual banks and extreme values

### Our Analysis Pipeline

We calculate DD/PD using four Jupyter notebooks:

1. **`dd_pd_accounting.ipynb`** → Calculates DD using balance sheet data
2. **`dd_pd_market.ipynb`** → Calculates DD using stock market data
3. **`merging.ipynb`** → Combines both approaches with ESG data
4. **`trim.ipynb`** → Removes unusual banks and extreme values

**Final Output**: `esg_0718.csv` with 1,431 bank-year observations (2016-2023)
- Contains DD_a, PD_a (accounting)
- Contains DD_m, PD_m (market)
- Contains ESG scores and controls
- Includes all observations (excluded ones have DD = NaN)

### Theoretical Foundation

The foundation comes from Merton (1974), who viewed equity as a call option on firm assets. This was extended by Kealhofer, McQuown, and Vasicek (KMV) for publicly traded firms.

**Key References:**
- Merton, R. C. (1974). "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates"
- Bharath, S. T., & Shumway, T. (2008). "Forecasting Default with the Merton Distance to Default Model"
- Tepe, M., Thastrom, P., and Chang, R. (2022). "How Does ESG Activities Affect Default Risk"

---

## What is Distance to Default?

**Distance to Default (DD)** measures how many volatility steps separate a firm's assets from its debt level.

- **DD = 5**: Assets are 5 volatility steps above debt
- **DD = 1**: Only 1 volatility step from trouble
- **DD < 0**: Assets already below debt

---

## What is Probability of Default?

**Probability of Default (PD)** converts DD into a percentage chance of default within time T.

```
PD = Φ(-DD)
```

### Practical Interpretation

| DD | PD | Risk Level |
|----|-----|------------|
| 1 | 15.87% | Very High |
| 3 | 0.135% | High |
| 4.47 | 0.000391% | Moderate |
| 5 | 0.0000287% | Low |
| 5.7 | 5.99×10⁻⁷% | Very Low |
| ≥7 | ≈0†  | Very Low |

**†Note**: For DD ≥ 7, PD approaches machine precision limits. We report "effectively zero" and round to 3-4 significant digits only.

---

## The Merton Model Foundation

### Core Insight

Shareholders hold a **call option** on firm assets with strike price F.

### The Two Key Equations

#### 1. Equity Value Equation

```
E_t = V_t × Φ(d₁) - F_t × e^(-r_{f,t}×T) × Φ(d₂)
```

Where:
- **Φ(d₂)** = Risk-neutral probability V_T > F
- **Φ(d₁)** = Option delta (equity sensitivity to assets)

#### 2. Equity Volatility Equation

```
σ_{E,t-1} = (V_t/E_t) × Φ(d₁) × σ_{V,t}
```

### The d₁ and d₂ Terms

```
d₁ = [ln(V_t/F_t) + (r_{f,t} + 0.5×σ²_{V,t})×T] / (σ_{V,t}×√T)
d₂ = d₁ - σ_{V,t}×√T
```

**Derivation of d₂**:
```
d₂ = d₁ - σ_{V,t}×√T
   = [ln(V_t/F_t) + (r_{f,t} + 0.5×σ²_{V,t})×T] / (σ_{V,t}×√T) - σ_{V,t}×√T
   = [ln(V_t/F_t) + (r_{f,t} - 0.5×σ²_{V,t})×T] / (σ_{V,t}×√T)
```

### Critical Statement

**Distance to default equals d₂ when μ = r_f**:

```
DD = [ln(V_t/F_t) + (μ - 0.5×σ²_{V,t})×T] / (σ_{V,t}×√T)

When μ = r_{f,t}:
DD_m = d₂
PD_m = Φ(-d₂)
```

---

## Market-Based Approach

### Overview

Uses current market data to estimate default risk under the **risk-neutral (Q-measure)** where μ = r_{f,t}.

**Barrier Convention**: F_t = total liabilities (for banks).

**Rationale**: Deposits are liabilities and dominate bank funding. This follows standard practice for financial institutions.

**⏰ Timing Rule**: σ_{E,t-1} uses t-1 only, E_t, F_t, r_{f,t} are at t, unknowns V_t and σ_{V,t} are solved at t, horizon is t to t+1.

### Observable Inputs (with Timing)

| Variable | Symbol | Description | Units | Timing |
|----------|--------|-------------|-------|--------|
| Market Cap | E_t | Total share value | USD | t |
| Equity Vol | σ_{E,t-1} | Stock volatility | Decimal | t-1 |
| Total Liabilities | F_t | Total liabilities | USD | t |
| Risk-Free Rate | r_{f,t} | Safe return | Decimal | t |
| Time Horizon | T | Analysis period | Years | 1 |

**Data Source Note**: Millions converted to dollars once, not twice.

### Solver Process

**Initial Guesses**:
```
V₀ = E_t + F_t
σ_{V,0} = σ_{E,t-1}
```

**Convergence Criteria**:
- |E_model - E_t| < 10⁻⁶
- |σ_{E,model} - σ_{E,t-1}| < 10⁻⁴

**Solver Gates**: 
- Only converged solutions proceed to DD_m calculation
- Non-converged cases dropped from summaries
- Convergence rate reported in output

### Market DD and PD Formulas

```
DD_m = [ln(V_t/F_t) + (r_{f,t} - 0.5×σ²_{V,t})×T] / (σ_{V,t}×√T) = d₂

PD_m = Φ(-d₂)  [Q-measure probability]
```

### Market Variables Dictionary (with Timing)

| Variable | Symbol | Units | Timing | Role |
|----------|--------|-------|--------|------|
| `market_cap` | E_t | USD | t | Solver input |
| `equity_vol` | σ_{E,t-1} | Decimal | t-1 | Solver input |
| `total_liabilities_usd` | F_t | USD | t | Barrier |
| `rf` | r_{f,t} | Decimal | t | Drift |
| `asset_value` | V_t | USD | t | Solver output |
| `asset_vol` | σ_{V,t} | Decimal | t | Solver output |
| `DD_m` | DD_m | Std devs | t | Final metric |
| `PD_m` | PD_m | Probability | t | Q-measure |

---

## Accounting-Based Approach

### Overview

Uses balance sheet data with simplified proxies. Provides a **P-style score** when using μ̂ = r_{i,t-1}.

**Barrier Convention**: F_t = total liabilities (for banks).

**Rationale**: Deposits are liabilities and dominate bank funding. This follows standard practice for financial institutions.

**⏰ Timing Rule**: σ_{E,t-1} uses t-1 only, E_t, F_t are at t, μ̂_t = r_{i,t-1}, unknowns V̂_t and σ̂_{V,t} computed at t, horizon is t to t+1.

### Key Simplifications

1. **No solver**: Direct formulas
2. **Book values**: From financial statements  
3. **Drift**: μ̂ = r_{i,t-1} (previous year's equity return)

### Naive Proxies (Bharath-Shumway)

**Asset Value Proxy**:
```
V̂_t = Ê_t + F_t
```

**Asset Volatility Proxy**:
```
σ̂_{V,t} = (Ê_t/(Ê_t+F_t)) × σ_{E,t-1} + (F_t/(Ê_t+F_t)) × σ̂_{D,t}

where σ̂_{D,t} = 0.05 + 0.25 × σ_{E,t-1}
```

**Drift Proxy**:
```
μ̂ = r_{i,t-1}  (previous year's equity return)
```

### Equity Proxy for Banks

**Critical**: Book equity means total equity from balance sheet, not assets minus deposits or debt securities.

```
Ê_t = (Price-to-Book)_t × (Total Equity)_t
```

**Units**: Ensure consistent scaling (millions to dollars once).

### Accounting DD and PD Formulas

```
DD_a = [ln(V̂_t/F_t) + (μ̂ - 0.5×σ̂²_{V,t})×T] / (σ̂_{V,t}×√T)

PD_a = Φ(-DD_a)  [P-style score]
```

**Important**: This is a P-style score. **Calibrate to real PD via logit or hazard model if publishing PD.**

### Accounting Variables Dictionary (with Timing)

| Variable | Symbol | Units | Timing | Role |
|----------|--------|-------|--------|------|
| `total_equity` | - | Millions USD | t | Book equity source |
| `total_liabilities` | F_t | USD | t | Barrier |
| `E_proxy` | Ê_t | USD | t | P/B × equity |
| `sigma_E` | σ_{E,t-1} | Decimal | t-1 | Volatility input |
| `V_hat` | V̂_t | USD | t | Ê_t + F_t |
| `sigma_V_hat` | σ̂_{V,t} | Decimal | t | Weighted avg |
| `mu_hat` | μ̂ | Decimal | t-1 | r_{i,t-1} |
| `DD_a` | DD_a | Std devs | t | Final metric |
| `PD_a` | PD_a | Probability | t | P-style score |

---

## Comparing Both Approaches

| Aspect | Market (DD_m) | Accounting (DD_a) |
|--------|---------------|-------------------|
| **Measure** | Q-measure (risk-neutral) | P-style score |
| **Drift** | μ = r_{f,t} | μ̂ = r_{i,t-1} |
| **Asset Value** | Solved: V_t | Proxy: V̂_t = Ê_t + F_t |
| **Asset Vol** | Solved: σ_{V,t} | Proxy: σ̂_{V,t} |
| **Complexity** | High (solver) | Low (formulas) |
| **Use Case** | Trading, market risk | Credit, regulation |

---

## Data Quality: Trimming and Exclusions

### Why We Need Data Quality Controls

Not all banks are the same. Some have unusual business models that make DD calculations misleading. We need to exclude or adjust for:

1. **Low-Leverage Banks**: Banks with very little debt create artificially high DD values
2. **Extreme Outliers**: Statistical extremes that don't reflect real risk

### Two-Stage Approach

#### Stage 1: Excluding Unusual Banks (Before Calculation)

We **exclude** banks that don't fit the standard banking model:

**Low-Leverage Exclusion** (TD/TA < 2%):
- **What it means**: Banks with total debt less than 2% of total assets
- **Why exclude**: These are specialty banks (trust banks, asset managers) with different business models
- **The problem**: Very low debt (F) mechanically inflates DD = ln(V/F) / σ
- **Example**: EWBC (2018) had TD/TA = 1.41% → DD = 109.45 (unrealistically high)

**Other Exclusions**:
- **No debt** (F ≤ 0): Can't calculate DD without debt
- **Trivial debt** (F < $1M): Likely errors or inactive entities
- **Missing data**: Can't compute without required inputs

**Impact**:
```
Total observations: 1,431
Excluded for low leverage (TD/TA < 2%): 184 (12.9%)
Excluded for other reasons: ~60 (4.2%)
Valid for DD calculation: 1,187 (82.9%)
```

#### Stage 2: Trimming Extreme Values (After Calculation)

Even among normal banks, some DD values are extreme due to measurement noise or special circumstances.

**Year-Size Trimming**:
- Calculate DD for all valid banks
- Within each **year** and **size group** (large vs small/mid):
  - Remove bottom 1% (too risky to be realistic)
  - Remove top 1% (too safe to be realistic)

**Why year-size groups?**
- Different years have different risk levels (COVID vs normal times)
- Large banks have different DD patterns than small banks
- Prevents one group's extremes from affecting another

**Example**:
```
2018 Large Banks:
  - Before: DD_a ranges from 7.21 to 124.17
  - After trimming: DD_a ranges from 8.15 to 98.61
  - Removed: 3 observations (top/bottom 1%)

2020 Small Banks:
  - Before: DD_a ranges from 3.12 to 87.45
  - After trimming: DD_a ranges from 4.20 to 72.30
  - Removed: 2 observations
```

### What Happens to Excluded Data?

**Important**: Excluded observations **stay in the final dataset** but with DD = NaN.

This means:
- ESG scores preserved ✓
- Financial data preserved ✓
- You can analyze why they were excluded ✓
- DD/PD values set to NaN (can't use in regressions) ✓

**Status Codes** (in final dataset):
- `converged`: Successfully calculated (market approach)
- `included`: Successfully calculated (accounting approach)
- `low_leverage_td_ta`: Excluded for TD/TA < 2%
- `debt_too_low`: Excluded for debt < $1M
- `no_sigma_E`: Missing equity volatility
- `extreme_DD_a_y{year}_{size}`: Trimmed for extreme accounting DD
- `extreme_DD_m_y{year}_{size}`: Trimmed for extreme market DD

### Final Sample Summary

**After all exclusions and trimming**:

| Metric | Value |
|--------|-------|
| Total observations | 1,431 |
| DD_a available | 1,191 (83.2%) |
| DD_m available | 784 (54.8%) |
| Excluded (low leverage) | 184 (12.9%) |
| Excluded (no equity data) | 410 (28.6%) |
| Trimmed (extreme values) | ~40-50 (3-4%) |

**2018 Specific Impact** (our problematic year):
- Before leverage filter: DD_a mean = 28.88, max = 124.17
- After leverage filter: DD_a mean = 27.36, max = 114.23
- Improvement: -5.3% mean, -8.0% max

### How This Improves Our Analysis

1. **More Reliable DD Values**: No mechanical inflation from low-leverage banks
2. **Better Comparisons**: Banks are more similar (standard business models)
3. **Cleaner Regressions**: Outliers don't dominate statistical estimates
4. **Transparent**: All exclusions tracked and reported

### Simple Rule of Thumb

**For your analysis**:
- Use observations where `DD_a` or `DD_m` is **not NaN**
- Check `status` column to understand why others were excluded
- Report exclusion statistics in your paper's methods section

---

## Results Interpretation

### Current Sample Statistics (After Exclusions & Trimming)

**Final Dataset**: 1,431 total observations (2016-2023)

**DD_a (Accounting Distance-to-Default)**:
- Available: 1,191 observations (83.2%)
- Mean: ~18.5 standard deviations
- Median: ~16.0 standard deviations
- Range: 4.39 to 114.23

**DD_m (Market Distance-to-Default)**:
- Available: 784 observations (54.8%)
- Mean: ~11.5 standard deviations
- Median: ~9.2 standard deviations
- Range: 2.42 to 35.00 (capped by solver)

### What These Numbers Mean

**Typical Bank** (Median DD ≈ 16):
- Assets are **16 volatility steps** above debt
- Probability of default: **Φ(-16) ≈ 0%** (effectively zero)
- Very safe, well-capitalized

**Risky Bank** (DD ≈ 5):
- Assets are **5 volatility steps** above debt
- Probability of default: **0.000029%** (still very low)
- Normal for banking sector

**Why Banking DD Values Are High**:
1. Banks are heavily regulated (capital requirements)
2. Deposit insurance reduces actual default risk
3. Our 1-year horizon is short (less time for trouble)
4. We measure book liabilities as barrier (conservative)

### Comparing 2018 vs Other Years

**2018** (The Anomaly Year):
- Before leverage filter: Mean DD = 28.88
- After leverage filter: Mean DD = 27.36
- Still higher than other years due to 2-year volatility window

**2020** (COVID Year):
- Mean DD: ~15.5 (lower than 2018)
- Higher volatility → lower DD values
- Makes economic sense (more uncertainty)

**2022-2023** (Recent Years):
- Mean DD: ~17.0
- More stable, post-COVID normalization

### Interpretation Guide

| DD Range | PD | Risk Level | What It Means |
|----------|-----|------------|---------------|
| < 2 | > 2% | High Risk | Needs attention |
| 2-5 | 0.0003% - 2% | Moderate | Normal for small banks |
| 5-10 | < 0.00003% | Low | Typical large bank |
| 10-20 | ≈ 0% | Very Low | Well-capitalized |
| > 20 | ≈ 0% | Very Low | Very safe or low leverage |

---

## Walkthrough Examples

### Example 1: JPMorgan Chase (JPM) - 2019

#### Market Approach

**Step 1: Inputs (with timing)**

| Input | Value | Timing |
|-------|-------|--------|
| E_t | $387.4B | t |
| σ_{E,t-1} | 0.227 | t-1 |
| F_t | $516.1B | t |
| r_{f,t} | 0.0214 | t |
| T | 1 year | - |

**Step 2: Solver Output**

- V_t = $892.6B
- σ_{V,t} = 0.099

**Step 3: Calculate DD_m (showing intermediate steps)**

Numerator:
```
ln(V_t/F_t) + (r_{f,t} - 0.5×σ²_{V,t})×T
= ln(892.6/516.1) + (0.0214 - 0.5×0.099²)×1
= 0.548 + 0.0165
= 0.564
```

Denominator:
```
σ_{V,t}×√T = 0.099×1 = 0.099
```

DD_m:
```
DD_m = 0.564 / 0.099 = 5.70
```

**Step 4: Calculate PD_m**

```
PD_m = Φ(-5.70) = 5.99×10⁻⁷% (effectively zero)
```

### Example 2: Bank of America (BAC) - 2019

#### Market Approach

**Step 1: Inputs**

| Input | Value | Timing |
|-------|-------|--------|
| E_t | $265.3B | t |
| σ_{E,t-1} | 0.279 | t-1 |
| F_t | $430.2B | t |
| r_{f,t} | 0.0214 | t |

**Step 2: Solver Output**

- V_t = $686.3B
- σ_{V,t} = 0.108

**Step 3: Calculate DD_m (showing intermediate steps)**

Numerator:
```
ln(686.3/430.2) + (0.0214 - 0.5×0.108²)×1
= 0.467 + 0.0156
= 0.483
```

Denominator:
```
σ_{V,t}×√T = 0.108×1 = 0.108
```

DD_m:
```
DD_m = 0.483 / 0.108 = 4.47
```

**Step 4: Calculate PD_m**

```
PD_m = Φ(-4.47) = 0.000391% (3.91×10⁻⁴%)
```

### Comparison

| Bank | DD_m | PD_m | V_t | σ_{V,t} |
|------|------|------|-----|---------|
| JPM | 5.70 | 5.99×10⁻⁷% | $892.6B | 9.9% |
| BAC | 4.47 | 3.91×10⁻⁴% | $686.3B | 10.8% |

---

## Appendix: Why d₂ is the z-score of ln V_T vs ln F

### The Question

Under the Merton model, asset value V_t evolves as:

```
V_T = V_t × exp[(μ - 0.5×σ²_V)×T + σ_V×√T×Z]
```

where Z ~ N(0,1). Taking logs:

```
ln V_T = ln V_t + (μ - 0.5×σ²_V)×T + σ_V×√T×Z
```

Default occurs when V_T < F, or equivalently ln V_T < ln F.

### The z-score

The z-score measures how many standard deviations ln V_T is above ln F:

```
z = [E[ln V_T] - ln F] / SD[ln V_T]
  = [ln V_t + (μ - 0.5×σ²_V)×T - ln F] / (σ_V×√T)
  = [ln(V_t/F) + (μ - 0.5×σ²_V)×T] / (σ_V×√T)
  = DD
```

When μ = r_f (risk-neutral drift):

```
z = d₂
```

Therefore, **d₂ is the standardized distance between expected log asset value and log debt level**, measured in volatility units. The probability of default is:

```
P(ln V_T < ln F) = P(Z < -d₂) = Φ(-d₂)
```

This is why DD = d₂ and PD = Φ(-d₂) under the risk-neutral measure.

---

## Using the Final Dataset (esg_0718.csv)

### Quick Start for Analysis

**Step 1: Load the data**
```python
import pandas as pd
df = pd.read_csv('data/outputs/datasheet/esg_0718.csv')
```

**Step 2: Filter for valid DD observations**
```python
# For accounting DD analysis
df_accounting = df[df['DD_a'].notna()]

# For market DD analysis
df_market = df[df['DD_m'].notna()]

# For both
df_both = df[df['DD_a'].notna() & df['DD_m'].notna()]
```

**Step 3: Check exclusion reasons**
```python
# See why observations were excluded
print(df['status'].value_counts())

# Focus on included observations
df_included = df[df['status'].isin(['converged', 'included'])]
```

### Key Columns in Final Dataset

**Identifiers**:
- `instrument`: Bank ticker (e.g., 'JPM', 'BAC')
- `year`: Year (2016-2023)

**Default Risk Metrics**:
- `DD_a`: Accounting distance-to-default (NaN if excluded)
- `PD_a`: Accounting probability of default (NaN if excluded)
- `DD_m`: Market distance-to-default (NaN if excluded)
- `PD_m`: Market probability of default (NaN if excluded)

**ESG Scores**:
- `esg_score`: Overall ESG score
- `environmental_pillar_score`, `social_pillar_score`, `governance_pillar_score`

**Control Variables**:
- `lnta`: Log total assets (size)
- `td/ta`: Total debt to total assets (leverage)
- `price_to_book_value_per_share`: Valuation
- `dummylarge`, `dummymid`: Size categories

**Status**:
- `status`: Why observation was included/excluded

### Common Analysis Tasks

**Regression with DD_a**:
```python
# Drop excluded observations
reg_data = df[df['DD_a'].notna()].copy()

# Run regression
from statsmodels.formula.api import ols
model = ols('DD_a ~ esg_score + lnta + C(year)', data=reg_data).fit()
print(model.summary())
```

**Understanding Exclusions**:
```python
# Count exclusions by type
exclusions = df[df['DD_a'].isna()]['status'].value_counts()
print("\nExclusion reasons:")
print(exclusions)

# See low-leverage banks specifically
low_lev = df[df['status'] == 'low_leverage_td_ta']
print(f"\nLow leverage banks: {len(low_lev)}")
print(f"Mean TD/TA: {low_lev['td/ta'].mean():.4f} ({low_lev['td/ta'].mean()*100:.2f}%)")
```

**Compare 2018 to other years**:
```python
# 2018 vs others
df_2018 = df[(df['year'] == 2018) & (df['DD_a'].notna())]
df_other = df[(df['year'] != 2018) & (df['DD_a'].notna())]

print(f"2018 DD_a mean: {df_2018['DD_a'].mean():.2f}")
print(f"Other years DD_a mean: {df_other['DD_a'].mean():.2f}")
```

### Reporting in Your Paper

**Methods Section** (suggested language):

> "We calculate distance-to-default (DD) using both accounting and market approaches following Merton (1974) and Bharath & Shumway (2008). We exclude banks with total debt-to-asset ratios below 2% (184 observations, 12.9%) as their extremely low leverage creates mechanically inflated DD estimates. We then apply year-size percentile trimming (1st and 99th percentiles) to remove statistical outliers while preserving temporal and size-specific risk patterns. Our final sample includes 1,191 observations with accounting DD and 784 with market DD over 2016-2023."

**Results Section** (when describing sample):

> "Table 1 shows descriptive statistics for our sample. Mean DD_a is 18.5 (median 16.0), indicating that typical banks maintain substantial buffers above their debt levels. The corresponding default probabilities are effectively zero, consistent with the heavily regulated nature of the banking sector."

---

## References

1. Merton, R. C. (1974). "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates." *Journal of Finance*, 29(2), 449-470.

2. Bharath, S. T., & Shumway, T. (2008). "Forecasting Default with the Merton Distance to Default Model." *Review of Financial Studies*, 21(3), 1339-1369.

3. Tepe, M., Thastrom, P., and Chang, R. (2022). "How Does ESG Activities Affect Default Risk." FI Consulting White Paper.

4. Crosbie, P., & Bohn, J. (2003). "Modeling Default Risk." Moody's KMV Technical Document.

---

## Document Information

**Last Updated**: October 8, 2025  
**Version**: 2.0 (Includes leverage filter and current statistics)  
**Notebooks**: dd_pd_accounting.ipynb, dd_pd_market.ipynb, merging.ipynb, trim.ipynb  
**Final Dataset**: data/outputs/datasheet/esg_0718.csv (1,431 observations)
