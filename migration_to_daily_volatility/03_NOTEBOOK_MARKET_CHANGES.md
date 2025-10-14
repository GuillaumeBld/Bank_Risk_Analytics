# Market Notebook Changes
## dd_pd_market.ipynb - Step-by-Step Updates

**File**: `dd_pd_market.ipynb`  
**Estimated Time**: 1 hour  
**Difficulty**: Easy

---

## 📋 Overview

### What Changes in This Notebook

**Section 5: "Merge Equity Volatility"**

- ✅ **SIMPLE CHANGE**: Update filename from old to new
- ✅ **ADD**: Verification that daily volatility is being used
- ✅ **ADD**: Basic diagnostics

---

## 🎯 Step-by-Step Instructions

### STEP 1: Backup the Notebook

```bash
# In terminal
cp dd_pd_market.ipynb dd_pd_market_BACKUP_$(date +%Y%m%d).ipynb
```

### STEP 2: Open the Notebook

```bash
jupyter notebook dd_pd_market.ipynb
```

### STEP 3: Locate Section 5

**Find this cell** (should be around cell 10-12):

```markdown
## 5. Merge Equity Volatility
```

---

## 📝 Section 5 Updates

### OLD CODE (FIND THIS)

```python
## 5. Merge Equity Volatility

# Load equity volatility data
equity_vol = pd.read_csv('data/clean/equity_volatility_by_year.csv')

# Merge into main DataFrame
df = df.merge(
    equity_vol[['ticker_prefix','year','equity_volatility']],
    on=['ticker_prefix','year'],
    how='left'
)
df['equity_vol'] = df['equity_volatility']

print(f"\nEquity volatility merged: {df['equity_vol'].notna().sum()} rows")
```

### NEW CODE (REPLACE WITH THIS)

**Cell 1: Load Daily-Based Volatility**

```python
## 5. Merge Equity Volatility (Daily Returns, 252-Day Window)
"""
Loading equity volatility calculated from daily returns using 252-day window.
Method follows Bharath & Shumway (2008) academic standard.

Formula: σE,t-1 = SD(daily log returns in year t-1) × √252
"""

print("="*80)
print("SECTION 5: MERGE EQUITY VOLATILITY (DAILY-BASED)")
print("="*80)

# Load daily-based equity volatility
volatility_path = 'data/clean/equity_volatility_by_year_DAILY.csv'
equity_vol = pd.read_csv(volatility_path)

print(f"\nLoaded daily-based volatility:")
print(f"  Rows: {len(equity_vol)}")
print(f"  Years: {equity_vol['year'].min()} - {equity_vol['year'].max()}")
print(f"  Banks: {equity_vol['ticker'].nunique()}")

# Show calculation methods
print("\nCalculation Methods:")
print(equity_vol['method'].value_counts())
```

**Cell 2: Merge and Validate**

```python
# Merge into main DataFrame
print("\n" + "-"*80)
print("Merging volatility...")
print("-"*80)

before_merge = len(df)

df = df.merge(
    equity_vol[['ticker', 'year', 'sigma_E', 'method', 'days_used']],
    left_on=['ticker_prefix', 'year'],
    right_on=['ticker', 'year'],
    how='left',
    suffixes=('', '_vol')
)

# Use sigma_E as equity_vol for consistency with downstream code
df['equity_vol'] = df['sigma_E']

# Drop redundant ticker column
if 'ticker' in df.columns and 'ticker_prefix' in df.columns:
    df = df.drop(columns=['ticker'])

# Rename method column for clarity
df = df.rename(columns={
    'method': 'volatility_method',
    'days_used': 'volatility_days'
})

after_merge = len(df)

print(f"\nRows before merge: {before_merge}")
print(f"Rows after merge: {after_merge}")
print(f"Equity volatility coverage: {df['equity_vol'].notna().sum()} / {len(df)} ({df['equity_vol'].notna().mean()*100:.1f}%)")

# Validation checks
print("\n" + "="*80)
print("VALIDATION CHECKS")
print("="*80)

print("\n[1] Volatility Statistics:")
print(df['equity_vol'].describe())

print("\n[2] Missing Volatility by Year:")
missing_by_year = df[df['equity_vol'].isna()].groupby('year').size()
if len(missing_by_year) > 0:
    print(missing_by_year)
else:
    print("  ✅ No missing values!")

print("\n[3] Method Distribution:")
if 'volatility_method' in df.columns:
    print(df['volatility_method'].value_counts())

print("\n[4] Value Range Check (10%-100%):")
reasonable = df['equity_vol'].between(0.10, 1.0).sum()
total = df['equity_vol'].notna().sum()
print(f"  Within range: {reasonable} / {total} ({reasonable/total*100:.1f}%)")

if (df['equity_vol'] < 0.10).sum() > 0:
    print(f"  ⚠️  Below 10%: {(df['equity_vol'] < 0.10).sum()}")
if (df['equity_vol'] > 1.0).sum() > 0:
    print(f"  ⚠️  Above 100%: {(df['equity_vol'] > 1.0).sum()}")
```

**Cell 3: Visualization (Optional but Recommended)**

```python
# Quick visualization
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Distribution
ax1 = axes[0]
df['equity_vol'].hist(bins=40, ax=ax1, edgecolor='black', alpha=0.7)
ax1.axvline(df['equity_vol'].median(), color='red', linestyle='--', 
            label=f'Median: {df["equity_vol"].median():.3f}')
ax1.set_xlabel('Equity Volatility')
ax1.set_ylabel('Frequency')
ax1.set_title('Distribution of Equity Volatility\n(Daily Returns, 252-Day Window)')
ax1.legend()

# Over time
ax2 = axes[1]
vol_by_year = df.groupby('year')['equity_vol'].agg(['mean', 'median', 'std'])
vol_by_year[['mean', 'median']].plot(ax=ax2, marker='o')
ax2.fill_between(vol_by_year.index, 
                  vol_by_year['mean'] - vol_by_year['std'],
                  vol_by_year['mean'] + vol_by_year['std'],
                  alpha=0.2)
ax2.set_xlabel('Year')
ax2.set_ylabel('Equity Volatility')
ax2.set_title('Equity Volatility Over Time')
ax2.legend(['Mean', 'Median'])
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/outputs/analysis/market_equity_volatility.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n✅ Plot saved: data/outputs/analysis/market_equity_volatility.png")
```

**Cell 4: Final Status**

```python
# Final status
print("\n" + "="*80)
print("SECTION 5 COMPLETE: EQUITY VOLATILITY MERGED")
print("="*80)

print(f"\n✅ Volatility source: Daily returns with 252-day window (Bharath & Shumway 2008)")
print(f"✅ Coverage: {df['equity_vol'].notna().sum()} / {len(df)} ({df['equity_vol'].notna().mean()*100:.1f}%)")
print(f"✅ Mean volatility: {df['equity_vol'].mean():.3f}")
print(f"✅ Median volatility: {df['equity_vol'].median():.3f}")

if df['equity_vol'].isna().sum() > 0:
    print(f"\n⚠️  {df['equity_vol'].isna().sum()} rows missing volatility")
    print("   These will be excluded from solver")
else:
    print("\n✅ All rows have equity volatility")

print("\n→ Ready to proceed to Section 6 (Merton Solver)")
```

---

## ✅ Verification Checklist

After making changes:

### Technical Checks
- [ ] Cell runs without errors
- [ ] File path correct
- [ ] Merge completes successfully
- [ ] equity_vol column populated

### Value Checks
- [ ] Coverage ≥95%
- [ ] Values between 0.10 and 1.0
- [ ] Mean around 0.25-0.35

### Integration Checks
- [ ] Next sections use equity_vol correctly
- [ ] Solver runs without errors
- [ ] Output contains volatility info

---

## 📊 Expected Output

### Console Output

```
================================================================================
SECTION 5: MERGE EQUITY VOLATILITY (DAILY-BASED)
================================================================================

Loaded daily-based volatility:
  Rows: 1848
  Years: 2016 - 2023
  Banks: 231

Calculation Methods:
daily_252       1672
daily_partial    124
imputed_peer      52

--------------------------------------------------------------------------------
Merging volatility...
--------------------------------------------------------------------------------

Rows before merge: 1848
Rows after merge: 1848
Equity volatility coverage: 1848 / 1848 (100.0%)

================================================================================
VALIDATION CHECKS
================================================================================

[1] Volatility Statistics:
count    1848.000000
mean        0.285432
std         0.098765
min         0.125000
25%         0.215000
50%         0.268000
75%         0.335000
max         0.782000

[2] Missing Volatility by Year:
  ✅ No missing values!

[3] Method Distribution:
daily_252       1672
daily_partial    124
imputed_peer      52

[4] Value Range Check (10%-100%):
  Within range: 1848 / 1848 (100.0%)

================================================================================
SECTION 5 COMPLETE: EQUITY VOLATILITY MERGED
================================================================================

✅ Volatility source: Daily returns with 252-day window (Bharath & Shumway 2008)
✅ Coverage: 1848 / 1848 (100.0%)
✅ Mean volatility: 0.285
✅ Median volatility: 0.268
✅ All rows have equity volatility

→ Ready to proceed to Section 6 (Merton Solver)
```

---

## 🔍 Important Notes

### No Changes Needed in Other Sections

The rest of the notebook uses `equity_vol` column which we populated:

**Section 6 (Solver)**:
```python
# Already uses df['equity_vol'] - no changes needed
sigmaE_obs = row['equity_vol']
```

**Section 7 (Output)**:
```python
# Already includes equity_vol - no changes needed
output_cols = [..., 'equity_vol', ...]
```

### Downstream Effects

**Higher Volatility → Will Affect**:
1. **Solver convergence**: May take more iterations
2. **Asset volatility (σV)**: Will be higher
3. **Distance to Default (DD)**: Will be lower
4. **Probability of Default (PD)**: Will be higher

**This is EXPECTED and CORRECT** - daily volatility captures more market dynamics.

---

## 🔧 Troubleshooting

### Issue: FileNotFoundError

**Solution**:
```bash
# Make sure volatility calculator has been run
python migration_to_daily_volatility/05_VOLATILITY_CALCULATOR_SCRIPT.py

# Check file exists
ls -lh data/clean/equity_volatility_by_year_DAILY.csv
```

### Issue: Merge Reduces Rows

**Check ticker_prefix**:
```python
# In notebook
print("Unique tickers in df:", df['ticker_prefix'].nunique())
print("Unique tickers in equity_vol:", equity_vol['ticker'].nunique())

# Check for mismatches
in_df = set(df['ticker_prefix'].unique())
in_vol = set(equity_vol['ticker'].unique())
print("In df but not in vol:", in_df - in_vol)
print("In vol but not in df:", in_vol - in_df)
```

### Issue: Coverage Too Low

**Investigate**:
```python
# Find banks without volatility
missing = df[df['equity_vol'].isna()][['ticker_prefix', 'year', 'market_cap']]
print(missing.groupby('ticker_prefix').size().sort_values(ascending=False))

# Check if they have daily returns
import pandas as pd
daily = pd.read_csv('data/clean/raw_daily_total_return_2015_2023.csv')
daily['ticker_base'] = daily['Instrument'].str.replace(r'\.[A-Z]+$', '', regex=True)

for ticker in missing['ticker_prefix'].unique()[:5]:
    count = len(daily[daily['ticker_base'] == ticker])
    print(f"{ticker}: {count} daily observations")
```

---

## ✅ Completion

Once the cell runs successfully:

```python
# Continue to next section (Solver)
# No other changes needed in this notebook!

# After full run, export results
final_output.to_csv('data/outputs/datasheet/market_DAILY_volatility.csv', index=False)
print("✅ Market results exported with daily-based volatility")
```

---

**→ Next**: `04_DOCUMENTATION_UPDATES.md`
