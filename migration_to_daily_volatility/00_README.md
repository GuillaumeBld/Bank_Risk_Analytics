# Migration to Daily Volatility (252-Day Window)
## Complete Implementation Guide

**Date**: October 14, 2025  
**Objective**: Switch from 3-year annual returns to daily returns with 252-day window  
**Standard**: Bharath & Shumway (2008) methodology

---

## 📁 Folder Contents

```
migration_to_daily_volatility/
├── 00_README.md                           ← You are here
├── 01_MASTER_IMPLEMENTATION_PLAN.md       ← Start here: Overall strategy
├── 02_NOTEBOOK_ACCOUNTING_CHANGES.md      ← dd_pd_accounting.ipynb changes
├── 03_NOTEBOOK_MARKET_CHANGES.md          ← dd_pd_market.ipynb changes
├── 04_DOCUMENTATION_UPDATES.md            ← dd_and_pd.md changes
├── 05_VOLATILITY_CALCULATOR_SCRIPT.py     ← New volatility calculation script
├── 06_VALIDATION_TESTS.py                 ← Testing and validation
├── 07_COMPARISON_ANALYSIS.py              ← Before/After comparison
└── 08_ROLLBACK_INSTRUCTIONS.md            ← If something goes wrong
```

---

## 🎯 Quick Start

### Phase 1: Preparation (Day 1)
```bash
# 1. Backup everything
git checkout -b feature/daily-volatility
cp -r notebooks/ notebooks_BACKUP_$(date +%Y%m%d)/

# 2. Read the master plan
open 01_MASTER_IMPLEMENTATION_PLAN.md
```

### Phase 2: Calculate New Volatility (Day 1-2)
```bash
# 3. Run the volatility calculator
python migration_to_daily_volatility/05_VOLATILITY_CALCULATOR_SCRIPT.py
```

### Phase 3: Update Notebooks (Day 2-3)
```bash
# 4. Follow step-by-step guides
open 02_NOTEBOOK_ACCOUNTING_CHANGES.md
open 03_NOTEBOOK_MARKET_CHANGES.md
```

### Phase 4: Validation (Day 3)
```bash
# 5. Run tests
python migration_to_daily_volatility/06_VALIDATION_TESTS.py
python migration_to_daily_volatility/07_COMPARISON_ANALYSIS.py
```

### Phase 5: Documentation (Day 4)
```bash
# 6. Update paper
open 04_DOCUMENTATION_UPDATES.md
```

---

## ⚡ What Changes

### Old Method (Annual)
```python
# 3-year rolling window of annual returns
σE,t-1 = SD(rit: t-1, t-2, t-3)
# Already annual, no scaling needed
```

### New Method (Daily - Bharath & Shumway 2008)
```python
# 252-day window of daily returns from year t-1
σE,t-1 = SD(daily_log_returns: year t-1) × √252
# Use only year t-1 data (252 trading days)
```

---

## 📊 Expected Impact

| Metric | Change Expected |
|--------|----------------|
| **Volatility Values** | Higher (more granular data) |
| **DD Values** | Lower (higher volatility = riskier) |
| **PD Values** | Higher (more sensitive to risk) |
| **Correlation with Old** | ~0.7-0.8 |
| **2018 Crisis Impact** | Better captured |
| **COVID-19 Impact** | Better captured |

---

## ⏱️ Time Estimate

| Phase | Time | Who |
|-------|------|-----|
| Prepare & Backup | 30 min | You |
| Calculate Volatility | 2 hours | Script |
| Update Accounting NB | 2 hours | You + Script |
| Update Market NB | 1 hour | You + Script |
| Validation | 2 hours | Script |
| Update Documentation | 2 hours | You |
| **TOTAL** | **~10 hours** | **Over 3-4 days** |

---

## 🎓 Why This Change?

### Current (3-Year Annual)
- ❌ Not standard in literature
- ❌ No clear citation
- ❌ Less responsive to shocks
- ❌ Uses multiple years of data

### New (252-Day Daily)
- ✅ Bharath & Shumway (2008) standard
- ✅ Clear citation and methodology
- ✅ More responsive to market changes
- ✅ Uses only prior year data
- ✅ Standard in all DD literature

---

## 🔒 Safety Features

### Automated Backups
```bash
# All scripts create backups before making changes
notebooks_BACKUP_20251014/
data_BACKUP_20251014/
```

### Validation Checks
- ✅ No look-ahead bias verification
- ✅ Coverage checks (≥95% for 2016-2023)
- ✅ Correlation with old method (expected 0.7-0.8)
- ✅ Spot checks for major banks (JPM, BAC, WFC)

### Rollback Available
- See `08_ROLLBACK_INSTRUCTIONS.md` if needed

---

## 📞 Support

### If You Get Stuck

**Check the guides**:
1. `01_MASTER_IMPLEMENTATION_PLAN.md` - Overall strategy
2. Specific notebook change files (02, 03)
3. `08_ROLLBACK_INSTRUCTIONS.md` - Undo everything

**Common Issues**:
- Missing daily data → See Section 5 in Master Plan (imputation)
- Ticker mismatch → See Section 3 in Volatility Script
- Results look wrong → Run validation tests (06)

---

## ✅ Success Criteria

### Before Proceeding to Next Phase

**After Volatility Calculation**:
- [ ] File created: `data/clean/equity_volatility_by_year_DAILY.csv`
- [ ] Coverage ≥95% for years 2016-2023
- [ ] No NaN values for major banks

**After Notebook Updates**:
- [ ] Both notebooks run without errors
- [ ] DD/PD values are reasonable (no NaNs)
- [ ] Comparison report shows correlation ≥0.6

**After Validation**:
- [ ] All tests pass
- [ ] Spot checks verified
- [ ] Results documented

**After Documentation**:
- [ ] All "3-year" references updated
- [ ] Bharath & Shumway (2008) cited
- [ ] Methodology section updated

---

## 🚀 Ready to Start?

### Your Next Steps:

1. **Read This**: You're done! ✅

2. **Read Next**: `01_MASTER_IMPLEMENTATION_PLAN.md`
   - Detailed overall strategy
   - Prerequisites
   - Step-by-step timeline

3. **Then Execute**: Follow the guides in order (02 → 03 → 04)

---

## 📝 Notes

### Key Principles

1. **No Look-Ahead Bias**: Always use only year t-1 data for year t calculations
2. **252 Trading Days**: Standard annualization factor
3. **Log Returns**: Use log(1 + R/100) for normality
4. **Minimum 180 Days**: Need at least 70% of year for reliability

### Data Available

- **Daily Returns**: 2015-2023 (547,890 rows, 244 instruments)
- **Usable for DD**: 2016-2023 (need prior year data)
- **Coverage**: Excellent from 2015 onwards

---

*This migration ensures your analysis follows academic standards and can be properly cited in your research.*

**Good luck! 🎯**
