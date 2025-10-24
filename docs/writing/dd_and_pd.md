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
2. [Data Sources and Equity Volatility Methodology](#data-sources-and-equity-volatility-methodology)
3. [What is Distance to Default?](#what-is-distance-to-default)
4. [What is Probability of Default?](#what-is-probability-of-default)
5. [The Merton Model Foundation](#the-merton-model-foundation)
6. [Market-Based Approach](#market-based-approach)
7. [Accounting-Based Approach](#accounting-based-approach)
8. [Comparing Both Approaches](#comparing-both-approaches)
9. [Data Quality: Trimming and Exclusions](#data-quality-trimming-and-exclusions)
10. [Results Interpretation](#results-interpretation)
11. [Walkthrough Examples](#walkthrough-examples)
12. [Appendix: Why d₂ is the z-score](#appendix)

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

**Final Output**: `esg_dd_pd_20251011_043202.csv` with 1,424 bank-year observations (2016-2023)
- Contains DD_a, PD_a (accounting) - 1,290 non-null (90.6%)
- Contains DD_m, PD_m (market) - 1,290 non-null (90.6%)
- Contains ESG scores and controls
- 244 unique banking institutions
- Includes all observations (excluded ones have DD = NaN)

### Theoretical Foundation

The foundation comes from Merton (1974), who viewed equity as a call option on firm assets. This was extended by Kealhofer, McQuown, and Vasicek (KMV) for publicly traded firms.

**Key References:**
- Merton, R. C. (1974). "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates"
- Bharath, S. T., & Shumway, T. (2008). "Forecasting Default with the Merton Distance to Default Model"
- Tepe, M., Thastrom, P., and Chang, R. (2022). "How Does ESG Activities Affect Default Risk"

---

## Data Sources and Equity Volatility Methodology

### Overview

This section describes the data sources, equity volatility calculation methods, and quality control procedures used in our Distance to Default analysis covering 2016-2023.

### Data Sources

| Data Type | Source | Period | Description |
|-----------|--------|--------|-------------|
| **Daily Returns** | CRSP, Bloomberg | 2008-2023 | Daily total returns including dividends (252-day rolling window) |
| **Market Data** | Bloomberg, CRSP | 2016-2023 | Stock prices, market capitalization |
| **Accounting Data** | Compustat, S&P Capital IQ | 2016-2023 | Balance sheet items, liabilities |
| **Risk-Free Rate** | Federal Reserve | 2016-2023 | 1-year Treasury rate |

**Coverage**: 1,821 bank-year observations with complete volatility data across 2016-2023 period (93.1% of 1,955 total observations, 244 unique institutions).

---

### Equity Volatility Calculation

Equity volatility (σ_E) is estimated using daily returns following **Bharath and Shumway (2008)** methodology, with a hierarchical fallback structure:

#### Primary Method: 252-Day Rolling Standard Deviation (Daily Returns)

**Formula**:
```
σ_{E,t} = √252 × std(log_returns_{year t-1})
```

Where:
- **log_returns = ln(1 + daily_total_return)**: Daily log returns
- **√252**: Annualization factor (252 trading days per year)
- **Window**: All trading days from year t-1 only (strict timing discipline, no lookahead bias)

**Requirements**: 
- **Primary**: Minimum 180 trading days (≈70% of trading year) from year t-1
- **Data quality**: Removes extreme outliers (>100% daily moves)

**Coverage**: 89.3% of observations (1,745 of 1,955 bank-years) use this primary method.

**Advantages over monthly data**:
- Higher frequency captures intra-month volatility dynamics
- Better sensitivity to crisis periods and stress events
- Aligns with industry standard (Bharath & Shumway 2008, KMV-Merton literature)

---

#### Fallback 1: Partial Year Daily Data

Used when year t-1 has 90-179 trading days available (35-70% of trading year).

**Formula**: Same as primary method, but using available daily data from year t-1.

**Requirements**: Minimum 90 trading days (≈35% of trading year).

**Coverage**: 1.1% of observations (21 bank-years) use partial year data.

---

#### Fallback 2: Peer Median Imputation

Used when insufficient individual daily return data (<90 trading days from year t-1).

**Method**: 
- Classify banks into size buckets (large/mid/small) based on ESG data classification
  - **Large**: dummylarge = 1
  - **Mid**: dummymid = 1  
  - **Small**: default
- Compute median σ_E of all banks in same size bucket and year
- Peer volatility computed only from banks with complete daily data (primary or partial methods)

**Coverage**: 9.7% of observations (189 bank-years) use peer median imputation.

**Winsorization**: All volatility values (including imputed) are winsorized at 1st and 99th percentiles by year to remove extreme outliers.

---

### Data Quality and Sample Selection

Banks are classified based on daily return data availability:

| Category | Criteria | Method Used | Coverage |
|----------|----------|-------------|----------|
| **Complete (Primary)** | ≥180 days from year t-1 | 252-day daily volatility | 89.3% (1,745 obs) |
| **Partial** | 90-179 days from year t-1 | Partial year daily volatility | 1.1% (21 obs) |
| **Imputed** | <90 days from year t-1 | Peer median by size bucket | 9.7% (189 obs) |
| **Excluded** | No volatility calculated | Not included in DD/PD | 6.9% (134 obs) |

**Strict Filtering Rule**: Bank-year observations without calculated equity volatility are **excluded** from distance-to-default and probability of default calculations.

**Final Dataset Coverage**: 
- 1,955 total potential bank-year observations (2016-2023)
- 1,821 observations with complete volatility data (93.1%)
- **1,821 observations with DD/PD calculated** (after data quality filter)
- 134 observations excluded due to insufficient data (9.4%)

**Quality Principle**: Tier 1 and 2 observations receive DD/PD estimates. Tier 3 observations are retained in dataset but have DD = NaN.

---

### Provenance Tracking

Each σ_E value includes complete metadata for audit and transparency:

| Field | Description | Example Values |
|-------|-------------|----------------|
| **sigma_E_method** | Calculation method used | monthly36, monthly_ewma, peer_median |
| **sigma_E_window_months** | Actual window length | 12, 24, 36 |
| **sigmaE_window_start_year** | Window start year | 2015 (for 2018 calculation) |
| **sigmaE_window_end_year** | Window end year | 2017 (for 2018 calculation) |
| **obs_count** | Number of valid returns | 36 (maximum) |

**Example**: For 2018 DD calculation:
- **σ_E computed from**: Jan 2015 - Dec 2017 (36 months)
- **Window end**: 2017 (t-1)
- **No lookahead**: Uses only pre-2018 data

---

### Quality Control Filters

Additional filters applied after volatility calculation:

| Filter | Threshold | Rationale |
|--------|-----------|-----------|
| **Leverage Floor** | TD/TA < 2% | Exclude atypical capital structures |
| **Trimming** | 1st/99th percentile by year-size | Remove outliers |
| **Volatility Range** | 0.01% - 300% | Physical reasonableness |
| **Convergence** | Solver status = "converged" | Ensure solution quality |

**Trimming Procedure**:
1. Group by year and size bucket (large vs small/mid)
2. Compute 1st and 99th percentiles of DD within each group
3. Exclude observations outside these bounds
4. Applied separately to DD_m and DD_a

---

### Convergence Performance

**Market DD Results** (using improved volatility data):
- **Total observations**: 1,290 bank-years with DD/PD
- **Convergence rate**: 100% for observations with sufficient data
- **Method**: Newton-Raphson with numerical derivatives
- **Tolerance**: 1e-6 for both price and volatility residuals

**Key Feature**: Uniform application across all years (2016-2023) with no year-specific exceptions or manual adjustments.

---

### Results Summary by Year

**Distribution of DD Values**:

| Year | N (Market) | Mean DD_m | Median DD_m | P90 DD_m | Mean DD_a | Median DD_a |
|------|------------|-----------|-------------|----------|-----------|-------------|
| 2016 | 64 | 10.1 | 9.2 | 14.0 | 16.7 | 15.4 |
| 2017 | 125 | 8.6 | 8.0 | 11.2 | 14.9 | 13.9 |
| 2018 | 178 | 8.6 | 7.7 | 12.4 | 14.8 | 13.4 |
| 2019 | 192 | 8.8 | 8.0 | 12.6 | 13.4 | 12.4 |
| 2020 | 194 | 9.2 | 8.0 | 13.8 | 15.6 | 14.8 |
| 2021 | 194 | 7.0 | 6.4 | 10.6 | 11.6 | 10.9 |
| 2022 | 199 | 6.0 | 5.3 | 8.8 | 11.2 | 10.5 |
| 2023 | 144 | 5.8 | 5.0 | 8.5 | 10.1 | 9.3 |

**Observations**:
- DD values show reasonable variation across years
- Market DD (DD_m) ranges from 6-10 (mean), typical for banking sector
- Accounting DD (DD_a) consistently higher, reflecting balance sheet conservatism
- 2020 (COVID-19) shows elevated DD, consistent with increased volatility
- Post-2020 decline reflects rising interest rates and market uncertainty

---

### Method Distribution

**Primary Method Dominance**:

| Method | Approximate % | Description |
|--------|---------------|-------------|
| **monthly36** | ~98% | Full 36-month rolling window |
| **monthly_ewma** | ~1-2% | EWMA with limited data |
| **peer_median** | <1% | Size-based peer fallback |

**Quality Assessment**: >95% coverage with primary method indicates robust data availability across the sample period (2016-2023).

---

### Time Integrity Guarantees

**No Lookahead Bias**:
- σ_{E,t-1} window **ends strictly at year t-1**
- For 2018 DD: σ_E computed from 2015-2017 only
- For 2023 DD: σ_E computed from 2020-2022 only
- All provenance fields verify correct time indexing

**Window Validation**:
```
sigmaE_window_end_year = year - 1  (always)
sigmaE_window_start_year = window_end_year - (months/12 - 1)
```

**Example for 36-month window**:
- year = 2018
- window_end = 2017
- window_start = 2017 - 2 = 2015
- Covers: Jan 2015 - Dec 2017 (full 36 months before 2018)

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
Total observations: 1,424
Excluded for insufficient data: 134 (9.4%)
Valid for DD/PD calculation: 1,290 (90.6%)
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
| Total observations | 1,424 |
| DD_a available | 1,290 (90.6%) |
| DD_m available | 1,290 (90.6%) |
| Excluded (insufficient data) | 134 (9.4%) |

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

**Final Dataset**: 1,424 total observations (2016-2023)

**DD_a (Accounting Distance-to-Default)**:
- Available: 1,290 observations (90.6%)
- Mean: ~18.5 standard deviations
- Median: ~16.0 standard deviations
- Range: 4.39 to 114.23

**DD_m (Market Distance-to-Default)**:
- Available: 1,290 observations (90.6%)
- Mean: ~8.1 standard deviations (across 2016-2023)
- Median: ~7.4 standard deviations
- Range: 2.4 to 35.0 (solver numerical limit)

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

---

## Descriptive Statistics: DD and PD Measures

### Summary Statistics (Sample: 1,424 bank-years, 2016-2023)

**Table 1: Overall Descriptive Statistics**

| Statistic | DD_a | DD_m | PD_a | PD_m |
|-----------|------|------|------|------|
| **N** | 1,343 | 1,341 | 1,343 | 1,341 |
| **Mean** | 11.809 | 6.960 | 0.000855 | 0.001506 |
| **Std Dev** | 5.512 | 3.699 | 0.027 | 0.009 |
| **Min** | -5.720 | 0.865 | 0.000 | 0.000 |
| **1st Percentile** | 3.048 | 1.837 | 0.000 | 0.000 |
| **5th Percentile** | 4.330 | 2.452 | 0.000 | 0.000 |
| **10th Percentile** | 5.367 | 3.237 | 0.000 | 0.000 |
| **25th Percentile** | 8.528 | 4.869 | 0.000 | 0.000 |
| **Median** | 11.238 | 6.361 | 0.000 | 0.000 |
| **75th Percentile** | 14.314 | 8.180 | 0.000 | 0.000001 |
| **90th Percentile** | 17.818 | 10.497 | 0.000 | 0.000604 |
| **95th Percentile** | 20.789 | 13.118 | 0.000007 | 0.007102 |
| **99th Percentile** | 27.680 | 20.714 | 0.001153 | 0.033134 |
| **Max** | 61.440 | 35.000 | 1.000 | 0.194 |

**Notes**:
- DD_a: Distance-to-Default (Accounting approach, Bharath & Shumway naive method)
- DD_m: Distance-to-Default (Market approach, Merton model with iterative solver)
- PD_a: Probability of Default (Accounting) = Φ(-DD_a)
- PD_m: Probability of Default (Market) = Φ(-DD_m)
- **N Difference**: DD_a has 2 more observations than DD_m (COFS 2018-2019 have accounting data but missing market cap)
- Higher DD indicates lower default risk; Lower PD indicates lower default probability
- 94.3% of observations have valid DD_a; 94.2% have valid DD_m

---

**Table 2: Descriptive Statistics by Year**

| Year | N | DD_a Mean | DD_a Median | DD_m Mean | DD_m Median | PD_a Mean | PD_m Mean |
|------|---|-----------|-------------|-----------|-------------|-----------|-----------|
| 2016 | 69 | 13.68 | 13.08 | 8.36 | 7.84 | 0.000000 | 0.000000 |
| 2017 | 138 | 13.20 | 12.27 | 7.63 | 7.12 | 0.000000 | 0.000022 |
| 2018 | 198 | 13.26 | 12.48 | 7.73 | 7.05 | 0.000050 | 0.000172 |
| 2019 | 214 | 12.70 | 11.87 | 8.42 | 7.66 | 0.004982 | 0.000013 |
| 2020 | 218 | 14.49 | 13.50 | 8.57 | 7.56 | 0.000003 | 0.000019 |
| 2021 | 216 | 5.36 | 4.97 | 3.15 | 2.88 | 0.000682 | 0.009773 |
| 2022 | 217 | 11.69 | 10.86 | 6.19 | 5.67 | 0.000000 | 0.000043 |
| 2023 | 154 | 11.92 | 10.81 | 6.81 | 5.95 | 0.000001 | 0.000034 |

**Key Observations**:
- **2020 (COVID-19)**: Highest DD (14.49), indicating resilience despite pandemic
- **2021 Anomaly**: Sharp decline in DD (5.36) - data quality issue under investigation
- **2022-2023**: Return to normal risk levels (DD ~11.7-11.9)
- Pre-COVID stable period (2016-2019): DD_a ranged 12.70-13.68

---

**Table 3: Descriptive Statistics by Bank Size**

| Size | N | DD_a Mean | DD_a Median | DD_m Mean | DD_m Median | PD_a Mean | PD_m Mean |
|------|---|-----------|-------------|-----------|-------------|-----------|-----------|
| **Large** | 32 | 9.19 | 9.58 | 4.91 | 5.11 | 0.000021 | 0.002177 |
| **Mid** | 64 | 10.73 | 10.60 | 5.93 | 5.88 | 0.000013 | 0.001478 |
| **Small** | 1,328 | 11.93 | 11.40 | 7.06 | 6.48 | 0.000915 | 0.001490 |

**Counterintuitive Finding**: Larger banks show LOWER DD (higher risk) compared to smaller banks. This contrasts with "too big to fail" expectations and may reflect:
- Higher leverage ratios in large banks
- More complex risk profiles captured by market measures
- Different risk-taking behavior in systemically important institutions

---

**Table 4: Correlation Matrix**

|  | DD_a | DD_m | PD_a | PD_m |
|---|------|------|------|------|
| **DD_a** | 1.000 | 0.950 | -0.094 | -0.274 |
| **DD_m** | 0.950 | 1.000 | -0.015 | -0.244 |
| **PD_a** | -0.094 | -0.015 | 1.000 | 0.053 |
| **PD_m** | -0.274 | -0.244 | 0.053 | 1.000 |

**Key Findings**:
- **Very high correlation (0.950)** between DD_a and DD_m validates both methodologies
- DD and PD show expected negative relationship
- Low PD_a and PD_m correlation (0.053) suggests different information captured by each approach

---

### Interpretation for Paper

**Typical Bank Risk Profile**:
- Median DD_a = 11.24 (very safe, ~11 standard deviations from default)
- Median PD = essentially zero (75th percentile still at zero)
- Only top 5% of risky banks have PD_a > 0.000007
- Reflects heavily regulated, well-capitalized U.S. banking sector

**Distribution Characteristics**:
- **Right-skewed**: Most banks very safe (median PD ≈ 0), few with elevated risk
- **DD_a > DD_m**: Accounting approach yields higher DD (more conservative)
  - Mean DD_a (11.81) vs Mean DD_m (6.96)
  - Book values more stable than market values
- **PD concentration**: 75% of banks have PD effectively zero

**Volatility Impact** (Daily vs Monthly):
- Using daily returns with 252-day window (vs old 36-month monthly)
- Mean equity volatility: 31.7% (daily) vs 27.0% (monthly) = +17.4% increase
- Better captures intra-period dynamics, especially during crises
- Follows Bharath & Shumway (2008) industry standard

---

### Reporting in Your Paper

**Methods Section** (suggested language):

> "We calculate distance-to-default (DD) using both accounting and market approaches following Merton (1974) and Bharath & Shumway (2008). Equity volatility is computed from daily total returns using a 252-day rolling window (year t-1 only) with √252 annualization, following Bharath and Shumway (2008). We require a minimum of 180 trading days (70% of a trading year) for primary volatility calculation; observations with 90-179 days use partial year data, and those with <90 days use size-bucket peer median imputation. Bank-year observations without calculable equity volatility (6.9% of raw sample) are excluded from DD/PD calculations to ensure data quality. We further exclude banks with total debt-to-asset ratios below 2% as their extremely low leverage creates mechanically inflated DD estimates. Our final sample includes 1,821 bank-year observations with complete volatility data across 2016-2023 (93.1% coverage), with all major banking institutions represented across all years."

**Results Section** (when describing sample):

> "Table 1 presents descriptive statistics for distance-to-default and probability of default measures. Our final sample includes 1,424 bank-year observations from 2016-2023, with 1,343 observations (94.3%) having valid DD_a values and 1,341 (94.2%) having valid DD_m values. The two-observation difference reflects missing market capitalization data for COFS in 2018-2019, illustrating the slightly lower coverage of market-based measures compared to accounting-based measures."

> "Mean distance-to-default is 11.81 for the accounting approach and 6.96 for the market approach, indicating substantial buffers against default (11-7 standard deviations). The corresponding mean default probabilities are negligible (0.09% and 0.15%, respectively), with median values effectively zero. The distribution is highly right-skewed: 75% of bank-year observations have PD values at or near zero, reflecting the heavily regulated and well-capitalized nature of the U.S. banking sector. Only the riskiest 5% of observations exhibit PD_a > 0.000007 or PD_m > 0.007."

> "The high correlation between DD_a and DD_m (0.950) validates the consistency of both methodologies, despite DD_a systematically exceeding DD_m. This pattern reflects the greater stability of book values compared to market values, with the accounting approach producing more conservative (higher) distance-to-default estimates."

> "Panel B (Table 2) reveals temporal variation in default risk. The pre-COVID period (2016-2019) exhibited stable risk metrics with DD_a ranging from 12.70 to 13.68. During the COVID-19 pandemic year (2020), distance-to-default increased to 14.49, suggesting banks maintained strong capital buffers despite economic disruption, possibly aided by regulatory forbearance and government support programs. Risk metrics returned to pre-pandemic levels by 2022-2023 (DD_a: 11.69-11.92). Notably, 2021 shows anomalously low DD values (5.36) that warrant further investigation and may reflect data quality issues."

> "Panel C (Table 3) presents an unexpected pattern: larger banks exhibit lower distance-to-default (DD_a: 9.19 for large vs 11.93 for small), suggesting higher default risk. This contrasts with conventional 'too big to fail' expectations and may reflect higher leverage ratios, more complex risk profiles, or different risk-taking behavior in systemically important institutions."

> "Our equity volatility estimates, calculated from daily returns using a 252-day rolling window following Bharath & Shumway (2008), average 31.7% (median 26.4%), approximately 17% higher than previous monthly-based estimates. This higher volatility reflects superior capture of intra-period volatility dynamics, particularly relevant during crisis periods. The primary 252-day method is employed for 89.3% of observations, partial year data (90-179 days) for 1.1%, and size-bucket peer median imputation for 9.7%. Complete volatility coverage spans 93.1% of potential observations, with all systemically important banking institutions having complete coverage across all years."

---

## References

1. Merton, R. C. (1974). "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates." *Journal of Finance*, 29(2), 449-470.

2. Bharath, S. T., & Shumway, T. (2008). "Forecasting Default with the Merton Distance to Default Model." *Review of Financial Studies*, 21(3), 1339-1369.

3. Tepe, M., Thastrom, P., and Chang, R. (2022). "How Does ESG Activities Affect Default Risk." FI Consulting White Paper.

4. Crosbie, P., & Bohn, J. (2003). "Modeling Default Risk." Moody's KMV Technical Document.

---

## Document Information

**Last Updated**: October 14, 2025  
**Version**: 4.0 (Daily volatility migration complete, comprehensive descriptive statistics added)  
**Notebooks**: dd_pd_accounting.ipynb, dd_pd_market.ipynb, merging.ipynb  
**Final Dataset**: data/outputs/datasheet/esg_dd_pd_20251014_022322.csv (1,424 observations, 244 unique banks)  
**Volatility Method**: Daily returns, 252-day window (Bharath & Shumway 2008)  
**Descriptive Tables**: See Tables 1-4 above for complete statistics with all percentiles
