# Master Implementation Plan
## Daily Volatility Migration - Complete Strategy

**Date**: October 14, 2025  
**Estimated Time**: 3-4 days  
**Difficulty**: Moderate

---

## 📋 Executive Summary

### What We're Changing

**FROM**:
```
σE,t-1 = SD(annual returns: years t-1, t-2, t-3)
- 3-year rolling window
- Annual returns (rit)
- Min 2 observations
```

**TO**:
```
σE,t-1 = SD(daily log returns: year t-1) × √252
- 252-day window (1 year)
- Daily returns
- Min 180 trading days
```

### Why

1. **Academic Standard**: Bharath & Shumway (2008) - most cited DD paper
2. **Better Sensitivity**: Captures recent market movements
3. **Proper Citation**: Can reference specific methodology
4. **More Data**: 252 observations vs 3 observations

---

## 🎯 Implementation Timeline

### Day 1: Setup & Volatility Calculation (4 hours)

**Morning (2 hours)**:
```bash
# Hour 1: Backup and setup
git checkout -b feature/daily-volatility
cp -r notebooks/ notebooks_BACKUP_20251014/
cp -r data/clean/ data_BACKUP_20251014/

# Hour 2: Review daily data
python -c "
import pandas as pd
daily = pd.read_csv('data/clean/raw_daily_total_return_2015_2023.csv')
print(f'Shape: {daily.shape}')
print(f'Instruments: {daily[\"Instrument\"].nunique()}')
print(f'Date range: {daily[\"Date\"].min()} to {daily[\"Date\"].max()}')
"
```

**Afternoon (2 hours)**:
```bash
# Hour 3-4: Calculate new volatility
python migration_to_daily_volatility/05_VOLATILITY_CALCULATOR_SCRIPT.py

# Verify output
# Should create: data/clean/equity_volatility_by_year_DAILY.csv
```

### Day 2: Update Accounting Notebook (3 hours)

**Follow**: `02_NOTEBOOK_ACCOUNTING_CHANGES.md`

**Tasks**:
1. Update Section 5 (equity volatility)
2. Add comparison plots
3. Verify DD/PD calculations
4. Export new results

### Day 3: Update Market Notebook & Validate (3 hours)

**Morning (1 hour)**:
- Follow: `03_NOTEBOOK_MARKET_CHANGES.md`
- Update volatility loading
- Re-run solver

**Afternoon (2 hours)**:
```bash
# Run validation tests
python migration_to_daily_volatility/06_VALIDATION_TESTS.py

# Run comparison analysis
python migration_to_daily_volatility/07_COMPARISON_ANALYSIS.py
```

### Day 4: Documentation (2 hours)

**Follow**: `04_DOCUMENTATION_UPDATES.md`

**Update**:
- `docs/writing/dd_and_pd.md`
- `docs/guides/EQUITY_VOLATILITY_EXPLANATION.md`
- README.md

---

## 📂 File Changes Overview

### New Files Created

```
data/clean/
├── equity_volatility_by_year_DAILY.csv      ← NEW: Daily-based volatility
├── daily_returns_cleaned.csv                ← NEW: Cleaned daily returns
└── volatility_diagnostic_DAILY.csv          ← NEW: Coverage report

migration_to_daily_volatility/
├── [All migration files]                    ← NEW: This folder

data/outputs/datasheet/
├── esg_dd_pd_DAILY_[timestamp].csv          ← NEW: Results with daily vol
```

### Modified Files

```
dd_pd_accounting.ipynb                       ← MODIFIED: Section 5
dd_pd_market.ipynb                           ← MODIFIED: Section 5
docs/writing/dd_and_pd.md                    ← MODIFIED: Methodology section
```

### Backup Files (Auto-created)

```
notebooks_BACKUP_20251014/
data_BACKUP_20251014/
data/clean/equity_volatility_by_year.csv.OLD ← OLD: Keep for comparison
```

---

## 🔧 Prerequisites

### Data Requirements

✅ **You Have**:
- `data/clean/raw_daily_total_return_2015_2023.csv` (547,890 rows)
- `data/clean/List_bank.xlsx` (ticker mapping)
- `data/clean/ticker_mapping_exceptions.csv` (ticker corrections)

✅ **Auto-Generated**:
- Daily returns cleaned file
- New volatility file

### Software Requirements

```bash
# Python packages (already installed)
pandas
numpy
scipy
matplotlib
seaborn
```

### Knowledge Requirements

- ✅ Basic Python
- ✅ Jupyter notebooks
- ✅ Git (for backup)
- ⚠️ Understanding of volatility calculation (provided in guides)

---

## 📊 Detailed Methodology

### Step 1: Clean Daily Returns

**Input**: `raw_daily_total_return_2015_2023.csv`

**Process**:
```python
# 1. Parse dates
daily['Date'] = pd.to_datetime(daily['Date'], format='%m/%d/%y')

# 2. Standardize tickers
daily['ticker_base'] = daily['Instrument'].apply(standardize_ticker)

# 3. Convert to log returns
daily['return_decimal'] = daily['Total Return'] / 100
daily['log_return'] = np.log(1 + daily['return_decimal'])

# 4. Flag outliers (keep but flag)
daily['outlier'] = (daily['log_return'].abs() > 0.30)  # >30% daily move
```

**Output**: `data/clean/daily_returns_cleaned.csv`

### Step 2: Calculate Volatility for Each Bank-Year

**For each bank i, year t**:

```python
def calculate_sigma_E(bank, year_t):
    # Get year t-1 daily data
    year_tminus1 = year_t - 1
    start = f'{year_tminus1}-01-01'
    end = f'{year_tminus1}-12-31'
    
    data = daily_returns[
        (daily_returns['ticker'] == bank) &
        (daily_returns['date'] >= start) &
        (daily_returns['date'] <= end)
    ]
    
    n_days = len(data)
    
    if n_days >= 180:  # PRIMARY: Need 70% of year
        log_returns = data['log_return'].dropna()
        daily_std = log_returns.std()
        sigma_E = daily_std * np.sqrt(252)
        method = 'daily_252'
        flag = None
        
    elif n_days >= 90:  # FALLBACK A: Partial year
        log_returns = data['log_return'].dropna()
        daily_std = log_returns.std()
        sigma_E = daily_std * np.sqrt(252)
        method = 'daily_partial'
        flag = 'insufficient_days'
        
    else:  # FALLBACK B: Peer median
        sigma_E = get_peer_median(bank, year_tminus1)
        method = 'imputed'
        flag = 'no_daily_data'
    
    return {
        'ticker': bank,
        'year': year_t,
        'sigma_E': sigma_E,
        'method': method,
        'days_used': n_days,
        'flag': flag
    }
```

**Critical Rules**:
1. ⚠️ **NO LOOK-AHEAD**: Only use year t-1 data for year t
2. ✅ **252 Factor**: Always multiply daily SD by √252
3. ✅ **Log Returns**: Always use log(1+R), not raw R
4. ✅ **Minimum**: Require 180 days (70% of year)

### Step 3: Handle Edge Cases

**Missing Data**:
```python
# If bank has <180 days in year t-1
# → Use peer median (same size bucket)

size_buckets = {
    'large': dummylarge == 1,
    'mid': dummymid == 1,
    'small': (dummylarge == 0) & (dummymid == 0)
}

peer_median = df[
    (df['year'] == year_tminus1) &
    (df['size_bucket'] == bank_size) &
    (df['sigma_E'].notna())
]['sigma_E'].median()
```

**Outlier Days**:
```python
# Keep outlier days but flag them
# Do NOT remove unless clearly erroneous (e.g., >100% daily move)
daily['outlier_severe'] = daily['log_return'].abs() > 1.0  # >100%
# Remove only severe outliers
daily_clean = daily[~daily['outlier_severe']]
```

**Winsorization**:
```python
# After calculation, winsorize within each year
results['sigma_E_winsorized'] = results.groupby('year')['sigma_E'].transform(
    lambda x: x.clip(
        lower=x.quantile(0.01),
        upper=x.quantile(0.99)
    )
)
```

---

## 🔍 Validation Strategy

### Test 1: Timing Discipline

**Verify no look-ahead bias**:
```python
# For 2019 DD, should only use 2018 daily data
test_data = get_data_for_calculation('JPM', 2019)
assert test_data['date'].max() < pd.Timestamp('2019-01-01')
assert test_data['date'].min() >= pd.Timestamp('2018-01-01')
```

### Test 2: Coverage Check

**Require 95%+ coverage for main years**:
```python
coverage = results.groupby('year').agg({
    'sigma_E': lambda x: (x.notna().sum() / len(x)) * 100
})

for year in range(2016, 2024):
    assert coverage.loc[year, 'sigma_E'] >= 95.0, f"Year {year} coverage too low"
```

### Test 3: Method Distribution

**Most banks should use primary method**:
```python
method_counts = results['method'].value_counts(normalize=True)
assert method_counts['daily_252'] > 0.80  # >80% should use full 252 days
```

### Test 4: Reasonableness Check

**Volatility should be within expected ranges**:
```python
# Typical bank equity volatility: 15% - 60%
assert results['sigma_E'].between(0.10, 1.0).all()

# Mean should be around 25-35%
mean_vol = results['sigma_E'].mean()
assert 0.20 < mean_vol < 0.50
```

### Test 5: Correlation with Old

**Should correlate but not be identical**:
```python
comparison = old_vol.merge(new_vol, on=['ticker', 'year'])
corr = comparison[['sigma_E_old', 'sigma_E_new']].corr().iloc[0, 1]

assert 0.60 < corr < 0.90  # Expect 0.7-0.8 typically
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: Ticker Mismatch

**Problem**: Daily return ticker doesn't match List_bank ticker

**Solution**:
```python
# Add to ticker_mapping_exceptions.csv
ABCB.N → ABCB
BAC.N → BAC
JPM.N → JPM
```

### Issue 2: Missing Days

**Problem**: Bank has gaps in daily returns

**Solution**:
```python
# Count only non-NaN observations
valid_days = data['log_return'].notna().sum()

# If valid_days < 180, use fallback
if valid_days < 180:
    use_peer_median()
```

### Issue 3: Extreme Values

**Problem**: Volatility seems too high/low

**Check**:
```python
# 1. Verify annualization
print(f"Daily std: {daily_std}")
print(f"Annual: {daily_std * np.sqrt(252)}")

# 2. Check for data errors
suspicious = results[
    (results['sigma_E'] > 0.80) |  # >80% annual vol
    (results['sigma_E'] < 0.10)    # <10% annual vol
]
print(suspicious)

# 3. Inspect raw returns
bank_returns = daily[daily['ticker'] == 'SUSPICIOUS_BANK']
print(bank_returns['log_return'].describe())
```

### Issue 4: Results Look Wrong

**Problem**: DD/PD values very different from old

**Expected**:
- ✅ Volatility higher → DD lower
- ✅ Volatility higher → PD higher
- ✅ Changes especially in crisis years (2018, 2020)

**Investigate**:
```python
# Compare year by year
for year in range(2016, 2024):
    old_mean = old_results[old_results['year']==year]['DD_a'].mean()
    new_mean = new_results[new_results['year']==year]['DD_a'].mean()
    print(f"{year}: Old={old_mean:.2f}, New={new_mean:.2f}, Delta={new_mean-old_mean:.2f}")
```

---

## 📈 Expected Results Changes

### Volatility Changes

**Overall**:
- Mean volatility: +15% to +30% higher
- Median volatility: +10% to +25% higher
- More dispersion (higher SD of volatility)

**By Year**:
```
2016-2017: Modest change (+10-15%)  ← Stable period
2018:      Large change (+25-40%)   ← Market volatility
2019:      Modest change (+10-20%)  ← Recovery
2020:      Large change (+40-60%)   ← COVID-19
2021-2023: Moderate change (+15-30%)
```

### DD Changes

**Direction**: Lower DD (higher volatility = appears riskier)

**Magnitude**:
- Mean DD: -1 to -3 points lower
- Range: Expect DD to compress (less extreme values)
- 2018, 2020: Largest changes

### PD Changes

**Direction**: Higher PD (higher volatility = higher default prob)

**Magnitude**:
- Mean PD: +50% to +200% higher (but still small absolute values)
- Example: 0.01% → 0.02% is "100% increase" but still very low

---

## 🎯 Success Metrics

### Technical Metrics

- [ ] **Coverage**: ≥95% for years 2016-2023
- [ ] **No Errors**: Both notebooks run completely
- [ ] **Reasonable Values**: All σE between 0.10 and 1.0
- [ ] **Method Success**: ≥80% use primary method (daily_252)
- [ ] **Correlation**: 0.60-0.90 with old method

### Quality Metrics

- [ ] **Timing Verified**: No look-ahead bias
- [ ] **Citations Added**: Bharath & Shumway (2008) referenced
- [ ] **Documentation Complete**: All files updated
- [ ] **Comparison Report**: Generated and reviewed

### Research Metrics

- [ ] **Defensible**: Can explain methodology in paper
- [ ] **Standard**: Matches academic literature
- [ ] **Transparent**: All steps documented
- [ ] **Reproducible**: Scripts can be re-run

---

## 🚀 Next Steps

You've read the master plan. Now:

1. ✅ **Understand**: You know what's changing and why
2. ➡️ **Execute**: Follow in order:
   - `05_VOLATILITY_CALCULATOR_SCRIPT.py` (run this)
   - `02_NOTEBOOK_ACCOUNTING_CHANGES.md` (follow this)
   - `03_NOTEBOOK_MARKET_CHANGES.md` (follow this)
   - `06_VALIDATION_TESTS.py` (run this)
   - `04_DOCUMENTATION_UPDATES.md` (follow this)

3. 🎯 **Validate**: Check success metrics above

---

## 📞 Quick Reference

### Key Formulas

```python
# Daily to Annual
σE = daily_std × √252

# Log Return
log_ret = np.log(1 + return_decimal)

# Peer Median
peer_σE = median(same_size_bucket, same_year)
```

### Key Files

```python
# Input
'data/clean/raw_daily_total_return_2015_2023.csv'

# Output
'data/clean/equity_volatility_by_year_DAILY.csv'

# Notebooks
'dd_pd_accounting.ipynb'  # Section 5
'dd_pd_market.ipynb'      # Section 5

# Documentation
'docs/writing/dd_and_pd.md'
```

### Key Parameters

```python
TRADING_DAYS_PER_YEAR = 252
MIN_DAYS_PRIMARY = 180      # 70% of year
MIN_DAYS_FALLBACK = 90      # 35% of year
WINSORIZE_PERCENTILES = (0.01, 0.99)
```

---

*Ready to start? Run the volatility calculator next!*

**→ Next File**: `05_VOLATILITY_CALCULATOR_SCRIPT.py`
