# Instruction 3: Next Steps & Validation

**Status**: Preparation Complete ✅  
**Date**: October 11, 2025

---

## ✅ **Completed**

1. ✅ **Fix 1**: Method naming standardized (`monthly36` only)
2. ✅ **Fix 2**: Early years coverage analyzed (2013-2015)
3. ✅ **Equity volatility updated**: New σ_E file with 2018 improvements
4. ✅ **Validation script created**: `scripts/validate_instruction3.py`

---

## 📋 **What Needs to Run**

### **Step 1: Execute DD Notebooks**

The notebooks are already configured to load the new `equity_volatility_by_year.csv`. You need to run them to generate updated DD values.

#### **Option A: Run via Jupyter**
```bash
# Open in Jupyter and execute all cells
jupyter notebook dd_pd_market.ipynb
jupyter notebook dd_pd_accounting.ipynb
```

#### **Option B: Run via nbconvert**
```bash
# Market DD
jupyter nbconvert --to notebook --execute dd_pd_market.ipynb \
  --output dd_pd_market_updated.ipynb

# Accounting DD  
jupyter nbconvert --to notebook --execute dd_pd_accounting.ipynb \
  --output dd_pd_accounting_updated.ipynb
```

#### **Option C: Run as Python scripts**
If the notebooks export to `.py` scripts, you can run:
```bash
python dd_pd_market.py
python dd_pd_accounting.py
```

---

### **Step 2: Locate Output Files**

After running the notebooks, find the output CSV files. They're typically in:
- `data/outputs/datasheet/dd_pd_market_results.csv`
- `data/outputs/datasheet/dd_pd_accounting_results.csv`

Or check the notebook output paths in the last cells.

---

### **Step 3: Run Validation Script**

Once you have the new DD outputs, run the validation script:

```bash
cd /Users/guillaumebld/Documents/Graduate_Research/Professor\ Abol\ Jalilvand/fall2025/risk_bank/risk_bank

python3 scripts/validate_instruction3.py \
  --equity_vol data/clean/equity_volatility_by_year.csv \
  --dd_market_new data/outputs/datasheet/dd_pd_market_results.csv \
  --dd_accounting_new data/outputs/datasheet/dd_pd_accounting_results.csv \
  --tier_diag data/clean/total_return_diagnostic.csv
```

**Optional**: If you have old baseline files for comparison:
```bash
python3 scripts/validate_instruction3.py \
  --equity_vol data/clean/equity_volatility_by_year.csv \
  --dd_market_new data/outputs/datasheet/dd_pd_market_results.csv \
  --dd_accounting_new data/outputs/datasheet/dd_pd_accounting_results.csv \
  --dd_market_old data/outputs/datasheet/dd_pd_market_results_old.csv \
  --dd_accounting_old data/outputs/datasheet/dd_pd_accounting_results_old.csv \
  --tier_diag data/clean/total_return_diagnostic.csv
```

---

## 📊 **Expected Validation Output**

The script will generate 5 acceptance checks:

### **[A] Convergence Rate**
```
year  size_bucket  conv_rate
2016  large        0.95
2016  small_mid    0.97
2017  large        0.96
...
```

### **[B] Distribution Summary**
```
year  metric      n    mean    p50    p90    p99    max
2016  DD_m new   163  15.23   14.5   22.1   28.3   35.2
2017  DD_m new   165  14.87   13.9   21.8   27.5   33.8
2018  DD_m new   182  13.45   12.3   19.2   25.1   31.2  ← Key improvement!
...
```

### **[C] 2018 Spot Check (20 banks)**
```
ticker_base  sigma_E_new  sigma_E_old  DD_m_new  DD_m_old  sigma_E_delta  DD_m_delta
JPM          0.2068       0.1500       12.34     18.45     0.0568         -6.11
BAC          0.2830       0.2100       11.23     16.78     0.0730         -5.55
WFC          0.2308       0.1800       13.56     19.23     0.0508         -5.67
...
```

**Expected**: DD_m_delta should be **negative** (DD decreased)

### **[D] Status Code Scan**
```
OK, only standard status codes present
```

### **[E] Tier Counts**
```
Tier 1: 1308
Tier 2: 0
Tier 3: 116
```

---

## ⚠️ **Validation Criteria**

### **PASS Conditions:**
- ✅ **[A]**: Convergence >90% for most year-size groups
- ✅ **[B]**: 2018 DD mean decreased by 20-40%
- ✅ **[C]**: All 20 banks show DD_m_delta < 0
- ✅ **[D]**: No "2018" in status flags
- ✅ **[E]**: Tier counts match (1308/0/116)

### **FAIL Conditions:**
- ❌ Convergence <80% for any year
- ❌ 2018 DD did not decrease
- ❌ Any "2018" specific flags found
- ❌ Tier counts changed

---

## 🔍 **Troubleshooting**

### **If notebooks fail to run:**
1. Check Python/pandas versions
2. Verify file paths in notebooks
3. Check for missing dependencies
4. Review notebook cell outputs for errors

### **If validation script fails:**
1. **"Missing file"**: Check output paths in notebook last cells
2. **Column not found**: Adjust `--ddm_col`, `--dda_col` flags
3. **No old baseline**: Remove `--dd_market_old` and `--dd_accounting_old` flags

### **If 2018 DD didn't decrease:**
- Verify new σ_E file is being loaded (check notebook merge step)
- Check σ_E values for 2018 in `equity_volatility_by_year.csv`
- Confirm no hard-coded σ_E overrides in notebooks

---

## 📂 **File Locations**

### **Inputs (Ready)**:
- ✅ `data/clean/equity_volatility_by_year.csv` (new σ_E)
- ✅ `data/clean/esg_0718_clean.csv` (main data)
- ✅ `data/clean/all_banks_marketcap_annual_2016_2023.csv`
- ✅ `data/clean/fama_french_factors_annual_clean.csv`

### **Notebooks to Run**:
- 📓 `dd_pd_market.ipynb`
- 📓 `dd_pd_accounting.ipynb`

### **Outputs (To Generate)**:
- 📄 `data/outputs/datasheet/dd_pd_market_results.csv`
- 📄 `data/outputs/datasheet/dd_pd_accounting_results.csv`

### **Validation**:
- 🔍 `scripts/validate_instruction3.py` (ready to run)

---

## ✅ **Success Indicators**

When validation completes successfully:
1. All 5 checks [A-E] pass
2. 2018 DD shows expected downward shift
3. No year-specific flags present
4. Convergence rates are high (>90%)

**Then proceed to Instruction 4**: Update paper methodology

---

## 🚀 **Quick Start Command**

```bash
# Navigate to project directory
cd /Users/guillaumebld/Documents/Graduate_Research/Professor\ Abol\ Jalilvand/fall2025/risk_bank/risk_bank

# Step 1: Run DD notebooks (choose one method)
jupyter notebook dd_pd_market.ipynb  # Open and run all cells
# OR
jupyter nbconvert --to notebook --execute dd_pd_market.ipynb --output dd_pd_market_updated.ipynb

# Step 2: Repeat for accounting
jupyter notebook dd_pd_accounting.ipynb
# OR  
jupyter nbconvert --to notebook --execute dd_pd_accounting.ipynb --output dd_pd_accounting_updated.ipynb

# Step 3: Run validation
python3 scripts/validate_instruction3.py \
  --equity_vol data/clean/equity_volatility_by_year.csv \
  --dd_market_new data/outputs/datasheet/dd_pd_market_results.csv \
  --dd_accounting_new data/outputs/datasheet/dd_pd_accounting_results.csv \
  --tier_diag data/clean/total_return_diagnostic.csv
```

---

**Status**: Ready to execute DD recalculation  
**Next**: Run notebooks → Validate results → Proceed to Instruction 4

*Guide prepared: October 11, 2025*
