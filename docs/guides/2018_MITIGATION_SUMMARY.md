# 2018 Anomaly - Quick Reference

**The Problem**: 2018 DD values were abnormally high (mean = 27.21, max = 124.17)

**Root Cause**: σ_E based on only 2016-2017 (bull market years) → Artificially low volatility → Inflated DD

**Status**: Partially mitigated, core issue remains

---

## What Was Done

### 1. Data Cleaning ✅
- **File**: `scripts/fix_duplicates.py`
- **Action**: Removed duplicate PNC 2018 rows
- **Result**: 6 rows removed

### 2. Low-Leverage Exclusion ✅
- **File**: `scripts/find_leverage_threshold.py`
- **Action**: Exclude banks with TD/TA < 2%
- **Result**: 184 rows excluded (12.9%)
- **2018 Impact**: DD_a max 124.17 → 114.23

### 3. Year-Size Trimming ✅
- **Method**: Remove top/bottom 1% within year-size groups
- **2018 Impact**: ~5 rows trimmed
- **Result**: DD_a max 114.23 → 98.61

### 4. Documentation ✅
- **Files**: 
  - `investigate_2018.py` (root cause)
  - `WHY_DD_M_IS_35_FOR_JPM_2018.md` (detailed)
  - `outlier.md` (catalog)

---

## Impact Summary

```
2018 DD_a Values:
  Raw:              mean=28.88  max=124.17
  After mitigation: mean=22.15  max=98.61
  Improvement:      -23.3%      -20.6%
```

---

## For New Return Data Integration

### Critical Decision: Remove Mitigations?

**Your new data provides 2015 returns** → Can calculate proper 3-year window for 2018

### Test First:
```python
# 1. Check 2015 coverage
coverage_2015 = new_data[new_data['year'] == 2015].shape[0]

# 2. Recalculate σ_E for 2018
sigma_E_new = std(returns_2015, returns_2016, returns_2017)

# 3. Compare
if sigma_E_new > sigma_E_old:
    print("✓ Problem fixed - consider removing mitigations")
else:
    print("⚠ Problem persists - keep mitigations")
```

### Recommendations:

| Mitigation | Keep? | Why? |
|------------|-------|------|
| Duplicate removal | ✅ YES | Data quality |
| Low-leverage exclusion | ✅ YES | Structural issue |
| Year-size trimming | ✅ YES | Best practice |
| 2018-specific flags | ❌ REMOVE | If data fixed |

---

## Quick Action Plan

1. ✅ Read full report: `2018_YEAR_MITIGATION_REPORT.md`
2. ⏭️ Integrate new return data
3. ⏭️ Check 2015 data quality
4. ⏭️ Recalculate 2018 σ_E and DD
5. ⏭️ Decide which mitigations to keep
6. ⏭️ Update documentation

---

**Bottom Line**: 2018 anomaly was a data limitation, not a methodology error. Your new data (2013-2023) should fix it. Test before removing any mitigations.

*See full report for details: `2018_YEAR_MITIGATION_REPORT.md` (742 lines)*
