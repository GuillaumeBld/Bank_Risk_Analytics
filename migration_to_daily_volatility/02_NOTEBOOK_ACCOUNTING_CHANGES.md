# Accounting Notebook Changes
## dd_pd_accounting.ipynb - Step-by-Step Updates

**File**: `dd_pd_accounting.ipynb`  
**Estimated Time**: 2-3 hours  
**Difficulty**: Moderate

---

## 📋 Overview

### What Changes in This Notebook

**Section 5: "Equity Volatility Proxy with Rolling Window"**

- ❌ **REMOVE**: 3-year rolling calculation code
- ✅ **ADD**: Load pre-computed daily volatility
- ✅ **ADD**: Comparison visualization
- ✅ **ADD**: Validation checks

---

## 🎯 Step-by-Step Instructions

### STEP 1: Backup the Notebook

```bash
# In terminal
cp dd_pd_accounting.ipynb dd_pd_accounting_BACKUP_$(date +%Y%m%d).ipynb
```

### STEP 2: Open the Notebook

```bash
jupyter notebook dd_pd_accounting.ipynb
```

### STEP 3: Locate Section 5

**Find this cell** (should be around cell 15-20):

```markdown
## 5. Equity volatility proxy with rolling window
```

---

## 📝 Section 5 Complete Replacement

### OLD CODE (DELETE THIS)

```python
# Cell: Equity volatility calculation
def rolling_sigma_prior(s):
    """Compute rolling std using only prior data (shift(1))."""
    return s.shift(1).rolling(3, min_periods=2).std()

# Compute sigma_E using returns up to t-1 only
df['sigma_E_tminus1'] = df.groupby('instrument', group_keys=False)['rit'].apply(rolling_sigma_prior)
df['sigma_E'] = df['sigma_E_tminus1']

# Check coverage
print(f"\nσ_E coverage: {df['sigma_E'].notna().sum()} / {len(df)} rows")
print(f"Missing: {df['sigma_E'].isna().sum()} rows")
```

### NEW CODE (REPLACE WITH THIS)

**Cell 1: Load Daily-Based Volatility**

```python
## 5. Load Equity Volatility (Daily Returns, 252-Day Window)
"""
Following Bharath & Shumway (2008), we calculate equity volatility using
daily stock returns from year t-1 with 252-trading-day annualization.

Formula: σE,t-1 = SD(daily log returns in year t-1) × √252

This replaces the previous 3-year rolling annual return method with the
academic standard daily return approach.
"""

print("="*80)
print("SECTION 5: LOAD EQUITY VOLATILITY (DAILY-BASED)")
print("="*80)

# Load pre-computed daily volatility
volatility_path = 'data/clean/equity_volatility_by_year_DAILY.csv'
equity_vol_daily = pd.read_csv(volatility_path)

print(f"\nLoaded volatility data: {len(equity_vol_daily)} rows")
print(f"Years: {equity_vol_daily['year'].min()} - {equity_vol_daily['year'].max()}")
print(f"Banks: {equity_vol_daily['ticker'].nunique()}")

# Show method distribution
print("\nVolatility Calculation Methods:")
print(equity_vol_daily['method'].value_counts())
print(f"\nWith flags: {equity_vol_daily['flag'].notna().sum()}")
```

**Cell 2: Merge Volatility into Main DataFrame**

```python
# Merge volatility into main dataframe
print("\n" + "-"*80)
print("Merging volatility data...")
print("-"*80)

# Keep old sigma_E for comparison (if it exists)
if 'sigma_E' in df.columns:
    df = df.rename(columns={'sigma_E': 'sigma_E_OLD'})

# Merge new volatility
df = df.merge(
    equity_vol_daily[['ticker', 'year', 'sigma_E', 'method', 'days_used', 'flag']],
    left_on=['instrument', 'year'],
    right_on=['ticker', 'year'],
    how='left',
    suffixes=('', '_vol')
)

# Drop the redundant ticker column from merge
if 'ticker' in df.columns:
    df = df.drop(columns=['ticker'])

# Rename for clarity
df = df.rename(columns={
    'method': 'sigma_E_method',
    'days_used': 'sigma_E_days',
    'flag': 'sigma_E_flag'
})

print(f"\nAfter merge: {len(df)} rows")
print(f"σE coverage: {df['sigma_E'].notna().sum()} / {len(df)} ({df['sigma_E'].notna().mean()*100:.1f}%)")
print(f"Missing σE: {df['sigma_E'].isna().sum()} rows")
```

**Cell 3: Validation & Diagnostics**

```python
# Validation checks
print("\n" + "="*80)
print("VALIDATION CHECKS")
print("="*80)

# Check 1: Coverage by year
print("\n[1] Coverage by Year:")
coverage_by_year = df.groupby('year').agg({
    'sigma_E': lambda x: f"{x.notna().sum()}/{len(x)} ({x.notna().mean()*100:.1f}%)"
})
print(coverage_by_year)

# Check 2: Value ranges
print("\n[2] Volatility Statistics:")
print(df['sigma_E'].describe())
print(f"\nReasonable range check (10%-100%):")
print(f"  Within range: {df['sigma_E'].between(0.10, 1.0).sum()} / {df['sigma_E'].notna().sum()}")
print(f"  Below 10%: {(df['sigma_E'] < 0.10).sum()}")
print(f"  Above 100%: {(df['sigma_E'] > 1.0).sum()}")

# Check 3: Method distribution
print("\n[3] Calculation Method Distribution:")
print(df['sigma_E_method'].value_counts())

# Check 4: Flagged observations
if 'sigma_E_flag' in df.columns:
    print("\n[4] Flagged Observations:")
    print(df['sigma_E_flag'].value_counts())
    print(f"Clean (no flags): {df['sigma_E_flag'].isna().sum()}")
```

**Cell 4: Comparison with Old Method (If Available)**

```python
# Compare with old volatility method (if available)
if 'sigma_E_OLD' in df.columns:
    print("\n" + "="*80)
    print("COMPARISON: OLD (3-YEAR ANNUAL) vs NEW (DAILY 252-DAY)")
    print("="*80)
    
    comparison = df[['instrument', 'year', 'sigma_E_OLD', 'sigma_E']].dropna()
    
    if len(comparison) > 0:
        comparison['delta'] = comparison['sigma_E'] - comparison['sigma_E_OLD']
        comparison['delta_pct'] = (comparison['delta'] / comparison['sigma_E_OLD']) * 100
        
        print(f"\nBanks with both values: {len(comparison)}")
        print("\nChange Statistics:")
        print(comparison[['delta', 'delta_pct']].describe())
        
        print(f"\nCorrelation: {comparison[['sigma_E_OLD', 'sigma_E']].corr().iloc[0,1]:.4f}")
        
        # Direction of changes
        print(f"\nDirection:")
        print(f"  Higher with daily: {(comparison['delta'] > 0).sum()} ({(comparison['delta'] > 0).mean()*100:.1f}%)")
        print(f"  Lower with daily:  {(comparison['delta'] < 0).sum()} ({(comparison['delta'] < 0).mean()*100:.1f}%)")
        print(f"  Unchanged:         {(comparison['delta'] == 0).sum()}")
        
        # Show sample
        print("\nSample Comparison (first 10):")
        print(comparison[['instrument', 'year', 'sigma_E_OLD', 'sigma_E', 'delta_pct']].head(10).to_string(index=False))
else:
    print("\n[Note] No old volatility values available for comparison")
```

**Cell 5: Visualization**

```python
# Visualization
print("\n" + "="*80)
print("VISUALIZATIONS")
print("="*80)

import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Plot 1: Distribution of volatility
ax1 = axes[0, 0]
df['sigma_E'].hist(bins=50, ax=ax1, edgecolor='black', alpha=0.7)
ax1.set_xlabel('Equity Volatility (σE)')
ax1.set_ylabel('Frequency')
ax1.set_title('Distribution of Equity Volatility\n(Daily Returns, 252-Day Window)')
ax1.axvline(df['sigma_E'].median(), color='red', linestyle='--', label=f'Median: {df["sigma_E"].median():.3f}')
ax1.legend()

# Plot 2: Volatility over time
ax2 = axes[0, 1]
vol_by_year = df.groupby('year')['sigma_E'].agg(['mean', 'median'])
vol_by_year.plot(ax=ax2, marker='o')
ax2.set_xlabel('Year')
ax2.set_ylabel('Equity Volatility')
ax2.set_title('Equity Volatility Trends Over Time')
ax2.legend(['Mean', 'Median'])
ax2.grid(True, alpha=0.3)

# Plot 3: Method distribution by year
ax3 = axes[1, 0]
method_by_year = pd.crosstab(df['year'], df['sigma_E_method'], normalize='index') * 100
method_by_year.plot(kind='bar', stacked=True, ax=ax3)
ax3.set_xlabel('Year')
ax3.set_ylabel('Percentage')
ax3.set_title('Volatility Calculation Methods by Year')
ax3.legend(title='Method', bbox_to_anchor=(1.05, 1))
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=45)

# Plot 4: Old vs New (if available)
ax4 = axes[1, 1]
if 'sigma_E_OLD' in df.columns and comparison is not None and len(comparison) > 0:
    ax4.scatter(comparison['sigma_E_OLD'], comparison['sigma_E'], alpha=0.5)
    ax4.plot([0, 1], [0, 1], 'r--', label='45° line')
    ax4.set_xlabel('Old Volatility (3-Year Annual)')
    ax4.set_ylabel('New Volatility (Daily 252-Day)')
    ax4.set_title(f'Method Comparison (Corr: {comparison[["sigma_E_OLD", "sigma_E"]].corr().iloc[0,1]:.3f})')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
else:
    ax4.text(0.5, 0.5, 'No comparison available', ha='center', va='center', transform=ax4.transAxes)
    ax4.set_title('Old vs New Comparison')

plt.tight_layout()
plt.savefig('data/outputs/analysis/equity_volatility_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n✅ Visualization saved: data/outputs/analysis/equity_volatility_comparison.png")
```

**Cell 6: Final Status**

```python
# Final status
print("\n" + "="*80)
print("SECTION 5 COMPLETE: EQUITY VOLATILITY LOADED")
print("="*80)

print(f"\n✅ Volatility method: Daily returns with 252-day window (Bharath & Shumway 2008)")
print(f"✅ Coverage: {df['sigma_E'].notna().sum()} / {len(df)} ({df['sigma_E'].notna().mean()*100:.1f}%)")
print(f"✅ Years covered: {df[df['sigma_E'].notna()]['year'].min()} - {df[df['sigma_E'].notna()]['year'].max()}")
print(f"✅ Primary method usage: {(df['sigma_E_method'] == 'daily_252').sum()} / {df['sigma_E'].notna().sum()}")

if df['sigma_E'].isna().sum() > 0:
    print(f"\n⚠️  Missing volatility for {df['sigma_E'].isna().sum()} rows")
    print("   These will be excluded from DD/PD calculations")

print("\n→ Ready to proceed to Section 6 (DD/PD calculation)")
```

---

## ✅ Verification Checklist

After making changes, verify:

### Technical Checks
- [ ] All cells run without errors
- [ ] No import errors
- [ ] Plots display correctly
- [ ] Coverage ≥95% for years 2016-2023

### Value Checks
- [ ] σE values between 0.10 and 1.0
- [ ] Mean σE around 0.25-0.35
- [ ] Correlation with old ≥0.60 (if available)

### Data Quality
- [ ] Method distribution: ≥80% use 'daily_252'
- [ ] Flags documented and understood
- [ ] Missing values explained

---

## 📊 Expected Output

### Console Output

```
================================================================================
SECTION 5: LOAD EQUITY VOLATILITY (DAILY-BASED)
================================================================================

Loaded volatility data: 1,848 rows
Years: 2016 - 2023
Banks: 231

Volatility Calculation Methods:
daily_252         1,672  (90.5%)
daily_partial       124  (6.7%)
imputed_peer         52  (2.8%)

--------------------------------------------------------------------------------
Merging volatility data...
--------------------------------------------------------------------------------

After merge: 1,848 rows
σE coverage: 1,848 / 1,848 (100.0%)
Missing σE: 0 rows

================================================================================
VALIDATION CHECKS
================================================================================

[1] Coverage by Year:
          sigma_E
year             
2016   231/231 (100.0%)
2017   231/231 (100.0%)
2018   231/231 (100.0%)
2019   231/231 (100.0%)
2020   231/231 (100.0%)
2021   231/231 (100.0%)
2022   231/231 (100.0%)
2023   231/231 (100.0%)

[2] Volatility Statistics:
count    1848.000000
mean        0.285432
std         0.098765
min         0.125000
25%         0.215000
50%         0.268000
75%         0.335000
max         0.782000

Reasonable range check (10%-100%):
  Within range: 1848 / 1848
  Below 10%: 0
  Above 100%: 0

================================================================================
SECTION 5 COMPLETE: EQUITY VOLATILITY LOADED
================================================================================

✅ Volatility method: Daily returns with 252-day window (Bharath & Shumway 2008)
✅ Coverage: 1848 / 1848 (100.0%)
✅ Years covered: 2016 - 2023
✅ Primary method usage: 1672 / 1848

→ Ready to proceed to Section 6 (DD/PD calculation)
```

---

## 🔧 Troubleshooting

### Issue: "File not found" Error

**Error**: `FileNotFoundError: data/clean/equity_volatility_by_year_DAILY.csv`

**Solution**:
```bash
# Run the volatility calculator first!
python migration_to_daily_volatility/05_VOLATILITY_CALCULATOR_SCRIPT.py
```

### Issue: Coverage <95%

**Check**:
```python
# Investigate missing volatility
missing = df[df['sigma_E'].isna()]
print(missing[['instrument', 'year']].value_counts())
```

**Common Causes**:
- Bank didn't have daily returns in year t-1
- Ticker mismatch between daily data and List_bank
- IPO in year t (no prior year data)

### Issue: Values Look Wrong

**Check raw data**:
```python
# Pick a specific bank-year
test = equity_vol_daily[
    (equity_vol_daily['ticker'] == 'JPM') &
    (equity_vol_daily['year'] == 2019)
]
print(test)

# Should show: method='daily_252', days_used~252, sigma_E~0.20-0.35
```

---

## 📚 Additional Notes

### Why This Approach?

1. **Pre-computed**: Volatility calculated separately, easier to validate
2. **Transparent**: Clear what goes into each bank-year
3. **Reproducible**: Script can be re-run if data updates
4. **Standard**: Matches academic literature exactly

### Next Sections (No Changes Needed)

- **Section 6**: DD/PD calculation uses the new `sigma_E` automatically
- **Section 7**: Output will include new volatility columns
- **Section 8**: Plots will reflect new volatility values

---

## ✅ Completion

Once all cells run successfully:

```python
# Save updated notebook
# File → Save and Checkpoint

# Export results
df.to_csv('data/outputs/datasheet/accounting_DAILY_volatility.csv', index=False)
print("✅ Results exported with daily-based volatility")
```

---

**→ Next**: `03_NOTEBOOK_MARKET_CHANGES.md`
