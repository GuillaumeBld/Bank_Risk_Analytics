# Daily Volatility Migration Plan
## Switching from Annual to Daily Total Returns

**Date**: October 14, 2025  
**Author**: Migration Plan  
**Objective**: Replace annual return-based equity volatility with daily return-based methodology following Bharath & Shumway (2008)

---

## Executive Summary

### Current State
- **Method**: 3-year rolling standard deviation of annual returns
- **Data**: Annual returns (rit) from 2016-2023
- **Window**: 3 years, minimum 2 observations
- **Annualization**: Already annual (no scaling needed)

### Target State
- **Method**: Rolling standard deviation of daily log returns  
- **Data**: Daily total returns from 2015-2023 (547,890 observations, 244 instruments)
- **Window**: 252 trading days (1 year) for year t-1
- **Annualization**: Daily SD × √252

---

## Data Availability

### Daily Total Return Coverage
```
Year    Instruments
2008        1
2014       12
2015      201  ← First full year
2016      205
2017      215
2018      224
2019      229
2020      231
2021      234
2022      236
2023      242
```

**File**: `data/clean/raw_daily_total_return_2015_2023.csv`  
**Format**: `Instrument, Total Return, Date`  
**Total rows**: 547,890

---

## Methodology: Bharath & Shumway (2008) Approach

### Core Formula

For bank `i` in year `t`:

```
σE,i,t-1 = SD(daily log returns in year t-1) × √252
```

**Where**:
- Use daily returns from January 1 to December 31 of year `t-1`
- Require minimum 180 trading days (≈70% of year)
- Log returns: `r_d = ln(1 + R_d/100)`
- Annualization factor: √252 (standard trading days per year)

### Timing Discipline (No Look-Ahead Bias)

**For 2019 DD calculation**:
```
Use daily returns: Jan 1, 2018 → Dec 31, 2018
Do NOT use: Any data from 2019
```

**Implementation**:
```python
cutoff_date = pd.Timestamp(f'{target_year}-01-01')
year_tminus1_start = pd.Timestamp(f'{target_year-1}-01-01')
year_tminus1_end = pd.Timestamp(f'{target_year-1}-12-31')

prior_data = daily_data[
    (daily_data['date'] >= year_tminus1_start) &
    (daily_data['date'] <= year_tminus1_end)
]
```

---

## Implementation Plan

### Phase 1: Data Preparation & Validation (Week 1)

#### 1.1 Clean Daily Return Data
**Script**: `scripts/01_prepare_daily_returns.py`

```python
# Standardize instrument tickers
# Handle missing dates (weekends, holidays)
# Convert returns to decimals
# Calculate log returns
# Flag suspicious values (outliers, zeros)
```

**Outputs**:
- `data/clean/daily_returns_cleaned.csv`
- `data/clean/daily_return_diagnostic.csv` (coverage report)

#### 1.2 Ticker Mapping
**Update**: Use existing `ticker_mapping_exceptions.csv`

```python
# Map daily return tickers to List_bank tickers
# Handle suffixes: .N, .O, .OQ, .K, etc.
# Validate all mappings
```

---

### Phase 2: Equity Volatility Calculation (Week 1-2)

#### 2.1 New Volatility Script
**Script**: `scripts/02_calculate_equity_volatility_DAILY.py`

**Priority Logic**:

```python
def calculate_sigma_E(bank_i, year_t):
    """
    Calculate equity volatility for bank i in year t
    using ONLY data from year t-1
    """
    
    # Step 1: Get daily returns for year t-1
    year_tminus1 = year_t - 1
    daily_returns = get_daily_returns(bank_i, year_tminus1)
    
    # Step 2: Check data quality
    n_days = len(daily_returns)
    
    if n_days >= 180:  # Min 180 trading days
        # PRIMARY METHOD: Year t-1 daily returns
        log_returns = np.log(1 + daily_returns / 100)
        daily_std = log_returns.std()
        sigma_E = daily_std * np.sqrt(252)
        method = 'daily_tminus1'
        flag = None
        
    elif n_days >= 90:  # 90-179 days available
        # FALLBACK A: Use available data with flag
        log_returns = np.log(1 + daily_returns / 100)
        daily_std = log_returns.std()
        sigma_E = daily_std * np.sqrt(252)
        method = 'daily_partial'
        flag = 'insufficient_days'
        
    else:
        # FALLBACK B: Peer median imputation
        sigma_E = get_peer_median(bank_i, year_tminus1)
        method = 'imputed_peer'
        flag = 'no_daily_data'
    
    return {
        'ticker': bank_i,
        'year': year_t,
        'sigma_E': sigma_E,
        'method': method,
        'days_used': n_days,
        'flag': flag
    }
```

**Winsorization**:
```python
# After calculation, winsorize within each year
results['sigma_E_winsorized'] = results.groupby('year')['sigma_E'].transform(
    lambda x: x.clip(lower=x.quantile(0.01), upper=x.quantile(0.99))
)
```

**Outputs**:
- `data/clean/equity_volatility_by_year_DAILY.csv`
- `data/clean/volatility_diagnostic_DAILY.csv`

---

### Phase 3: Update Notebooks (Week 2)

#### 3.1 Accounting Notebook (`dd_pd_accounting.ipynb`)

**Current Code** (Section 5):
```python
# OLD: Rolling 3-year annual returns
def rolling_sigma_prior(s):
    return s.shift(1).rolling(3, min_periods=2).std()

df['sigma_E'] = df.groupby('instrument')['rit'].apply(rolling_sigma_prior)
```

**New Code**:
```python
# NEW: Load pre-computed daily volatility
equity_vol_daily = pd.read_csv('data/clean/equity_volatility_by_year_DAILY.csv')

df = df.merge(
    equity_vol_daily[['ticker', 'year', 'sigma_E', 'method', 'days_used']],
    left_on=['instrument', 'year'],
    right_on=['ticker', 'year'],
    how='left',
    suffixes=('_old', '_daily')
)

df['sigma_E'] = df['sigma_E_daily']
```

**Validation Block**:
```python
# Compare old vs new volatility
comparison = df[['instrument', 'year', 'sigma_E_old', 'sigma_E_daily']].dropna()
comparison['delta'] = comparison['sigma_E_daily'] - comparison['sigma_E_old']
comparison['delta_pct'] = (comparison['delta'] / comparison['sigma_E_old']) * 100

print("\n[VOLATILITY COMPARISON]")
print(comparison.describe())
print(f"\nMean change: {comparison['delta_pct'].mean():.2f}%")
print(f"Median change: {comparison['delta_pct'].median():.2f}%")
```

#### 3.2 Market Notebook (`dd_pd_market.ipynb`)

**Current Code** (Section 5):
```python
equity_vol = pd.read_csv('equity_volatility_by_year.csv')
```

**New Code**:
```python
# Load daily-based volatility
equity_vol = pd.read_csv('equity_volatility_by_year_DAILY.csv')

# Same merge logic applies
df = df.merge(
    equity_vol[['ticker', 'year', 'sigma_E']],
    on=['ticker', 'year'],
    how='left'
)
```

---

### Phase 4: Documentation Updates (Week 2)

#### 4.1 Update Files

**Files to Modify**:
1. `docs/guides/EQUITY_VOLATILITY_EXPLANATION.md`
   - Change "3-year rolling" → "252-day (year t-1)"
   - Update formula from annual SD to daily SD × √252
   - Add Bharath & Shumway (2008) citation

2. `docs/reference/Market_approach`
   - Update equity_vol input description
   - Note daily-based calculation

3. `docs/reference/Accounting_approach`
   - Update sigma_E calculation section

4. `README.md`
   - Add note about daily return methodology

#### 4.2 New Documentation

**Create**: `docs/guides/DAILY_VS_ANNUAL_VOLATILITY_COMPARISON.md`

```markdown
# Comparison: Daily vs Annual Volatility

## Key Differences

| Aspect | Annual Method (Old) | Daily Method (New) |
|--------|-------------------|-------------------|
| Data frequency | Annual | Daily |
| Window | 3 years | 1 year (252 days) |
| Minimum obs | 2 years | 180 days |
| Annualization | None (already annual) | × √252 |
| Literature | Ad-hoc | Bharath & Shumway (2008) |

## Expected Impact on Results

- Daily volatility captures recent market movements better
- More responsive to short-term shocks (e.g., COVID-19)
- Standard in academic literature
- Likely higher volatility estimates (more granular data)
```

---

### Phase 5: Testing & Validation (Week 3)

#### 5.1 Unit Tests
**File**: `tests/test_daily_volatility.py`

```python
def test_timing_discipline():
    """Verify no look-ahead bias"""
    # For 2019, should only use 2018 data
    sigma_2019 = calculate_sigma_E('JPM', 2019)
    assert sigma_2019['year'] == 2019
    assert sigma_2019['data_year'] == 2018

def test_annualization():
    """Verify √252 scaling"""
    daily_std = 0.02
    expected = 0.02 * np.sqrt(252)  # ≈ 0.3175
    assert np.isclose(expected, 0.3175, rtol=0.01)

def test_minimum_days():
    """Require 180 days minimum"""
    # Test with 179 days → should use fallback
    # Test with 180 days → should use primary method
```

#### 5.2 Acceptance Criteria

**Coverage Check**:
```python
# Must have ≥95% coverage for 2016-2023
coverage = results.groupby('year').agg({
    'sigma_E': lambda x: x.notna().sum() / len(x) * 100
})
assert (coverage['sigma_E'] >= 95).all()
```

**Method Distribution**:
```python
# Expect majority to use primary method
method_counts = results['method'].value_counts(normalize=True)
assert method_counts['daily_tminus1'] > 0.80  # 80%+ primary
```

**Spot Check 2018**:
```python
# Compare JPM, BAC, WFC for 2018
test_banks = ['JPM', 'BAC', 'WFC']
old_vol = load_old_volatility(test_banks, 2018)
new_vol = load_new_volatility(test_banks, 2018)

comparison = pd.merge(old_vol, new_vol, on=['ticker', 'year'])
print(comparison)
# Manual verification: Are changes reasonable?
```

---

### Phase 6: Results Comparison & Analysis (Week 3-4)

#### 6.1 Volatility Comparison

**Script**: `scripts/compare_volatility_methods.py`

```python
# Load old and new volatility
old_vol = pd.read_csv('equity_volatility_by_year.csv')
new_vol = pd.read_csv('equity_volatility_by_year_DAILY.csv')

# Merge and compare
comparison = old_vol.merge(new_vol, on=['ticker', 'year'], 
                           suffixes=('_annual', '_daily'))

# Statistics
print(f"Mean volatility (annual): {comparison['sigma_E_annual'].mean():.4f}")
print(f"Mean volatility (daily):  {comparison['sigma_E_daily'].mean():.4f}")
print(f"Correlation: {comparison[['sigma_E_annual', 'sigma_E_daily']].corr().iloc[0,1]:.4f}")

# Visualizations
plt.scatter(comparison['sigma_E_annual'], comparison['sigma_E_daily'], alpha=0.5)
plt.xlabel('Annual Method')
plt.ylabel('Daily Method')
plt.title('Equity Volatility: Annual vs Daily')
plt.plot([0, 1], [0, 1], 'r--')  # 45-degree line
plt.savefig('docs/plots/volatility_comparison.png')
```

#### 6.2 DD/PD Impact Analysis

**Script**: `scripts/compare_dd_pd_results.py`

```python
# Re-run notebooks with new volatility
# Compare DD_a, DD_m, PD_a, PD_m

old_results = pd.read_csv('data/outputs/datasheet/esg_dd_pd_OLD.csv')
new_results = pd.read_csv('data/outputs/datasheet/esg_dd_pd_NEW.csv')

metrics = ['DD_a', 'DD_m', 'PD_a', 'PD_m']
for metric in metrics:
    print(f"\n{metric}:")
    print(f"  Old mean: {old_results[metric].mean():.4f}")
    print(f"  New mean: {new_results[metric].mean():.4f}")
    print(f"  Correlation: {old_results[metric].corr(new_results[metric]):.4f}")
```

---

## Implementation Timeline

```
Week 1 (Oct 14-20):
├── Day 1-2: Data cleaning & ticker mapping
├── Day 3-4: Implement new volatility calculation
└── Day 5:   Testing & validation

Week 2 (Oct 21-27):
├── Day 1-2: Update dd_pd_accounting.ipynb
├── Day 3-4: Update dd_pd_market.ipynb  
└── Day 5:   Documentation updates

Week 3 (Oct 28-Nov 3):
├── Day 1-2: Comprehensive testing
├── Day 3-4: Results comparison
└── Day 5:   Review & adjustments

Week 4 (Nov 4-10):
├── Day 1-3: Final validation & documentation
├── Day 4:   Generate comparison reports
└── Day 5:   Archive old method, deploy new
```

---

## Risk Mitigation

### Backup Strategy
```bash
# Before making changes
git checkout -b feature/daily-volatility-migration
cp -r notebooks/ notebooks_BACKUP_$(date +%Y%m%d)/
cp -r data/clean/ data/clean_BACKUP_$(date +%Y%m%d)/
```

### Rollback Plan
```bash
# If issues arise
git checkout main
# Restore from backup
cp -r notebooks_BACKUP_YYYYMMDD/* notebooks/
```

### Parallel Validation
- Keep old volatility calculations for 1 quarter
- Run both methods side-by-side
- Compare results before full cutover

---

## Acceptance Checklist

### Data Quality
- [ ] Daily returns loaded: 547,890 rows
- [ ] Ticker mapping: 100% coverage for main banks
- [ ] Missing data flagged and documented
- [ ] Outliers winsorized at 1%/99%

### Calculation Correctness
- [ ] No look-ahead bias (verified with spot checks)
- [ ] Annualization factor correct (√252)
- [ ] Minimum 180 days enforced
- [ ] Peer median imputation working

### Notebook Integration
- [ ] dd_pd_accounting.ipynb runs without errors
- [ ] dd_pd_market.ipynb runs without errors  
- [ ] DD/PD values reasonable (no NaNs, outliers)
- [ ] Comparison report generated

### Documentation
- [ ] EQUITY_VOLATILITY_EXPLANATION.md updated
- [ ] New comparison document created
- [ ] All references to "3-year rolling" replaced
- [ ] Bharath & Shumway (2008) cited

### Testing
- [ ] Unit tests pass (100% pass rate)
- [ ] Coverage ≥95% for 2016-2023
- [ ] Correlation with old method ≥0.7
- [ ] Spot checks verified manually

---

## References

**Bharath, S. T., & Shumway, T. (2008)**  
*Forecasting default with the Merton distance to default model*  
The Review of Financial Studies, 21(3), 1339-1369.

**Key Points**:
- Use 252 trading days for annualization
- Daily log returns preferred over monthly
- Standard approach in default prediction literature

---

## Questions & Answers

### Q1: Why switch from annual to daily?
**A**: Daily returns are standard in academic literature (Bharath & Shumway 2008), provide more granular information, and better capture recent market movements.

### Q2: Will DD/PD values change significantly?
**A**: Yes, expect changes because:
- More responsive to recent shocks
- Different time window (1 year vs 3 years)
- Likely higher volatility → lower DD, higher PD

### Q3: What if a bank has <180 trading days?
**A**: Use peer median imputation (same size bucket), flagged as 'imputed_peer'.

### Q4: How to handle ticker mismatches?
**A**: Use existing `ticker_mapping_exceptions.csv` and add new mappings as needed.

### Q5: Can we run both methods in parallel?
**A**: Yes! Keep old calculations for validation period, then deprecate after confidence is established.

---

*Last Updated: October 14, 2025*  
*Status: Ready for Implementation*
