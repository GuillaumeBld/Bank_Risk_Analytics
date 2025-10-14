# Rollback Instructions
## How to Undo the Migration if Needed

**Use this if**: Something went wrong and you need to revert to the old method

---

## 🚨 When to Rollback

### Rollback if:
- ❌ Validation tests fail badly (>10 failures)
- ❌ Results look completely wrong
- ❌ Notebooks won't run
- ❌ Coverage <80%
- ❌ You find a critical bug

### Don't rollback if:
- ✅ Just a few warnings (review and proceed)
- ✅ Small differences in results (expected)
- ✅ Minor ticker mismatches (fixable)

---

## 📦 Quick Rollback (Git-based)

### If You're on the Feature Branch

```bash
# Option 1: Discard all changes
git checkout main
git branch -D feature/daily-volatility

# Option 2: Keep changes but don't use them
git stash
git checkout main
```

### If You've Already Committed

```bash
# Revert to before migration
git log --oneline  # Find the commit before migration
git reset --hard COMMIT_HASH

# Or just checkout previous version of files
git checkout main -- dd_pd_accounting.ipynb
git checkout main -- dd_pd_market.ipynb
git checkout main -- docs/writing/dd_and_pd.md
```

---

## 📁 Manual Rollback (File-based)

### Step 1: Restore Backup Files

```bash
# Restore notebooks from backup
cp notebooks_BACKUP_20251014/dd_pd_accounting.ipynb dd_pd_accounting.ipynb
cp notebooks_BACKUP_20251014/dd_pd_market.ipynb dd_pd_market.ipynb

# Restore data files
cp data_BACKUP_20251014/equity_volatility_by_year.csv data/clean/equity_volatility_by_year.csv
```

### Step 2: Remove New Files

```bash
# Remove daily volatility file
rm data/clean/equity_volatility_by_year_DAILY.csv
rm data/clean/daily_returns_cleaned.csv
rm data/clean/volatility_diagnostic_DAILY.csv
```

### Step 3: Restore Documentation

```bash
# Restore old documentation
git checkout main -- docs/writing/dd_and_pd.md
git checkout main -- docs/guides/EQUITY_VOLATILITY_EXPLANATION.md
```

### Step 4: Clean Up

```bash
# Remove migration folder (optional)
rm -rf migration_to_daily_volatility/
```

---

## 🔄 Restore Accounting Notebook Section 5

### If You Only Need to Fix the Notebook

**Replace Section 5 with**:

```python
## 5. Equity volatility proxy with rolling window

def rolling_sigma_prior(s):
    """Compute rolling std using only prior data (shift(1))."""
    return s.shift(1).rolling(3, min_periods=2).std()

# Compute sigma_E using returns up to t-1 only
df['sigma_E_tminus1'] = df.groupby('instrument', group_keys=False)['rit'].apply(rolling_sigma_prior)
df['sigma_E'] = df['sigma_E_tminus1']

# Check coverage
print(f"\nσ_E coverage: {df['sigma_E'].notna().sum()} / {len(df)} rows")
print(f"Missing: {df['sigma_E'].isna().sum()} rows")

# Fallback: Use size-bucket median for missing values
size_groups = df.groupby(['year', 'size_bucket'])['sigma_E'].transform('median')
df['sigma_E'] = df['sigma_E'].fillna(size_groups)

# Winsorize
df['sigma_E'] = df.groupby('year')['sigma_E'].transform(
    lambda x: x.clip(lower=x.quantile(0.01), upper=x.quantile(0.99))
)

print(f"After fallback: {df['sigma_E'].notna().sum()} / {len(df)} rows")
```

---

## 🔄 Restore Market Notebook Section 5

### If You Only Need to Fix the Notebook

**Replace Section 5 with**:

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

---

## 📝 Restore Documentation

### dd_and_pd.md

**Key sections to restore**:

1. **Volatility Calculation**:
```markdown
### Equity Volatility Calculation

We calculate equity volatility (σ_E) using a 3-year rolling window of annual returns:

σ_{E,t-1} = SD(r_{t-1}, r_{t-2}, r_{t-3})

Where:
- r_t = annual equity return in year t
- Minimum 2 years of data required
- Uses only historical data (no look-ahead bias)
```

2. **Data Table**:
```markdown
| **Total Returns** | CRSP | 2013-2023 | Annual total returns (3-year lookback) |
```

---

## ✅ Verify Rollback Worked

### Test Old Setup

```bash
# 1. Check notebooks run
jupyter nbconvert --to notebook --execute dd_pd_accounting.ipynb
jupyter nbconvert --to notebook --execute dd_pd_market.ipynb

# 2. Check results match previous
python -c "
import pandas as pd
current = pd.read_csv('data/outputs/datasheet/esg_dd_pd_LATEST.csv')
old = pd.read_csv('data/outputs/datasheet/esg_dd_pd_PREVIOUS.csv')
print('Correlation:', current['DD_a'].corr(old['DD_a']))
# Should be ~1.0 if rollback successful
"
```

---

## 🔍 Troubleshooting Rollback

### Issue: Backup Files Not Found

**Solution**:
```bash
# Check backup location
ls -la notebooks_BACKUP_*/

# If no backup, get from git history
git log --all --full-history -- dd_pd_accounting.ipynb
git checkout COMMIT_HASH -- dd_pd_accounting.ipynb
```

### Issue: Notebooks Still Have Errors

**Solution**:
```bash
# Reset to known good state
git fetch origin
git checkout origin/main -- dd_pd_accounting.ipynb
git checkout origin/main -- dd_pd_market.ipynb
```

### Issue: Data Files Corrupted

**Solution**:
```bash
# Re-download or regenerate original files
# If you have a data backup
cp /path/to/original/backup/* data/clean/
```

---

## 📊 After Rollback: What to Check

### Critical Checks

- [ ] Both notebooks run without errors
- [ ] Results file generated
- [ ] DD/PD values look reasonable
- [ ] No references to "daily" or "252" in volatility context
- [ ] Documentation says "3-year rolling"

### Run This Test

```python
import pandas as pd

# Load results
df = pd.read_csv('data/outputs/datasheet/esg_dd_pd_LATEST.csv')

# Check basics
print(f"Rows: {len(df)}")
print(f"DD_a mean: {df['DD_a'].mean():.2f}")
print(f"DD_m mean: {df['DD_m'].mean():.2f}")
print(f"Years: {df['year'].min()} - {df['year'].max()}")

# Should look familiar from before migration
```

---

## 💡 Learn and Try Again

### If You Had to Rollback

**Before trying again**:

1. **Identify the issue**:
   - What went wrong?
   - Which test failed?
   - Was it data, code, or documentation?

2. **Fix the root cause**:
   - Update the migration scripts
   - Fix ticker mappings
   - Adjust thresholds

3. **Test more carefully**:
   - Run validation tests before updating notebooks
   - Test on subset of data first
   - Compare results step by step

4. **Get help**:
   - Review the guides again
   - Check the original papers
   - Ask for second opinion on results

---

## 🚀 Ready to Try Again?

### When You're Ready

```bash
# Start fresh
git checkout -b feature/daily-volatility-v2

# Make fixes
# ... fix what went wrong ...

# Try again
python migration_to_daily_volatility/05_VOLATILITY_CALCULATOR_SCRIPT.py
python migration_to_daily_volatility/06_VALIDATION_TESTS.py

# If tests pass, proceed with caution
```

---

## 📞 Emergency Contact

### If All Else Fails

**Preserve evidence**:
```bash
# Save everything for debugging
tar -czf migration_failed_$(date +%Y%m%d_%H%M%S).tar.gz \
    migration_to_daily_volatility/ \
    data/outputs/ \
    *.ipynb

# This archive can be sent for help/debugging
```

---

*Rollback instructions complete. Stay calm, follow the steps, and you'll be back to working state.*

**Remember**: It's okay to rollback! Better to have a working old method than a broken new method. You can always try the migration again after fixing issues.
