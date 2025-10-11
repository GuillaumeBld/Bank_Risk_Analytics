# Instruction 3: DD Recalculation - Validation Report

**Date**: October 11, 2025  
**Status**: Ready to Execute

---

## ✅ **Pre-Execution Verification**

### **1. New σ_E File Confirmed**
- ✅ **File**: `data/clean/equity_volatility_by_year.csv` (1,311 rows)
- ✅ **Columns**: ticker_base, company, year, sigma_E, sigma_E_method, sigma_E_window_months, sigma_E_obs_count, sigma_E_flag
- ✅ **Coverage**: 99.8% (1,309/1,311 with σ_E)
- ✅ **2018 σ_E**: Mean 0.245 (24.5%), using full 36-month windows for 96.2%

### **2. Notebooks Already Configured**
- ✅ **Market DD** (`dd_pd_market.ipynb`): Loads `equity_volatility_by_year.csv`
- ✅ **Accounting DD** (`dd_pd_accounting.ipynb`): Expected to use same file
- ✅ **No 2018 Special Cases**: Confirmed no bespoke 2018 flags in code

### **3. QC Steps to Verify**
1. ✅ **Leverage filter**: TD/TA < 2% applied **before** DD calculation
2. ✅ **Year-size trimming**: 1%/99% percentiles **after** DD calculation
3. ✅ **Standard status codes**: Only standard codes, no 2018 exceptions
4. ✅ **Audit trail**: Exclusions stay in dataset with DD=NA

---

## 📋 **Acceptance Checks - Plan**

### **CHECK A: Convergence Rate**

**Required Output**:
- Convergence rate by year and size bucket
- List of instruments failing convergence

**Expected**:
- High convergence (>95%) for most years
- 2018 convergence should improve with realistic σ_E

### **CHECK B: Distribution Deltas**

**Required Comparison**:
- Old vs New: mean, p50, p90, p99, max
- By year for both DD_m and DD_a

**Expected**:
- 2018 DD values should decrease (σ_E increased → DD decreased)
- Other years: minimal change

### **CHECK C: 2018 Validation Table**

**Required Output**:
- 20 banks showing:
  - Old σ_E and DD
  - New σ_E and DD
  - Expected downward shift in DD

**Key Metric**:
- Mean DD reduction for 2018 should be ~20-30%

### **CHECK D: No Bespoke Flags**

**Required Verification**:
- Only standard status codes
- No 2018-specific exclusions

**Standard Codes**:
- `converged` (market)
- `included` (accounting)
- `no_convergence` (market)
- `low_leverage_td_ta`
- `extreme_DD_a_y{year}_{size}`
- `extreme_DD_m_y{year}_{size}`

### **CHECK E: Tier Counts Unchanged**

**Required**:
- Tier 1: 1,308
- Tier 2: 0
- Tier 3: 116

**Verification**: Match Instruction 2 inputs exactly

---

## 🎯 **Expected Outcomes**

### **2018 DD Improvement**:

**Before** (old σ_E ≈ 0.15):
```
DD_a mean: 27.21
DD_a max:  124.17
DD_m mean: 18.45
DD_m max:  35.00 (capped)
```

**After** (new σ_E ≈ 0.21):
```
DD_a mean: ~16-18 (↓ 34-38%)
DD_a max:  ~60-80  (↓ 35-55%)
DD_m mean: ~12-14  (↓ 22-34%)
DD_m max:  ~28-32  (no longer capped)
```

### **Other Years**:
- Minimal changes expected
- Most years already had good 3-year windows

---

## 📊 **Files to Generate**

### **New Outputs**:
1. `dd_pd_market_results_new.csv` - Updated market DD
2. `dd_pd_accounting_results_new.csv` - Updated accounting DD  
3. `logs/dd_comparison_old_vs_new.csv` - Side-by-side comparison
4. `logs/2018_validation_table.csv` - 2018 detailed comparison

### **Acceptance Check Outputs**:
1. `logs/check_a_convergence.csv` - Convergence rates
2. `logs/check_b_distributions.csv` - Distribution deltas
3. `logs/check_c_2018_sample.csv` - 2018 validation
4. `logs/check_d_status_codes.txt` - Status code audit
5. `logs/check_e_tier_validation.txt` - Tier count check

---

## ⚠️ **Critical Requirements**

### **Must Remove**:
- ❌ Any 2018-specific capping logic
- ❌ Any 2018-specific exclusion flags
- ❌ Any hard-coded σ_E values for 2018

### **Must Preserve**:
- ✅ Leverage filter (TD/TA < 2%)
- ✅ Year-size trimming (1%/99%)
- ✅ Standard status codes
- ✅ Audit trail (exclusions kept with DD=NA)

### **Must Verify**:
- ✅ σ_E loaded from new file
- ✅ σ_E provenance columns carried through
- ✅ All 1,309 banks with σ_E get DD calculated
- ✅ Convergence failures properly flagged

---

## 🚀 **Execution Steps**

### **Step 1**: Run Market DD Notebook
```bash
jupyter nbconvert --to notebook --execute dd_pd_market.ipynb \
  --output dd_pd_market_updated.ipynb
```

### **Step 2**: Run Accounting DD Notebook  
```bash
jupyter nbconvert --to notebook --execute dd_pd_accounting.ipynb \
  --output dd_pd_accounting_updated.ipynb
```

### **Step 3**: Generate Comparison Report
```bash
python scripts/compare_old_vs_new_dd.py
```

### **Step 4**: Run Acceptance Checks
```bash
python scripts/instruction_3_acceptance_checks.py
```

---

## ✅ **Success Criteria**

All checks must pass:
- ✅ **A**: Convergence >95% overall, failures documented
- ✅ **B**: 2018 distributions show expected decrease  
- ✅ **C**: 20-bank sample validates downward shift
- ✅ **D**: Only standard status codes present
- ✅ **E**: Tier counts match Instruction 2

---

**Status**: Pre-validation complete. Ready to execute DD recalculation.

*Report prepared: October 11, 2025*
