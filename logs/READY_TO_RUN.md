# ✅ READY TO RUN - Complete Workflow

**Date**: October 11, 2025  
**Status**: All corrections applied, ready for execution

---

## ✅ **Corrections Applied:**

### **1. Peer Median Calculation** ✅
- **Fixed**: Only uses instruments with `sigma_E_method` in {monthly36, monthly_ewma}
- **Result**: Prevents imputed values from feeding into peer calculations
- **File updated**: `scripts/02_calculate_equity_volatility.py`
- **Re-run**: New `equity_volatility_by_year.csv` generated

### **2. Output Path Locking** ✅
- **Created**: `scripts/link_latest_dd_outputs.py` 
- **Purpose**: Creates fixed-name copies of timestamped outputs
- **Target paths**:
  - `data/outputs/datasheet/dd_pd_market_results.csv`
  - `data/outputs/datasheet/dd_pd_accounting_results.csv`

---

## 🚀 **Complete Execution Workflow**

### **Step 1: Run Market DD Notebook**

```bash
cd /Users/guillaumebld/Documents/Graduate_Research/Professor\ Abol\ Jalilvand/fall2025/risk_bank/risk_bank

# Open and run all cells
jupyter notebook dd_pd_market.ipynb
```

**Output**: Creates `data/outputs/datasheet/market_YYYYMMDD_HHMMSS.csv`

---

### **Step 2: Run Accounting DD Notebook**

```bash
# Open and run all cells
jupyter notebook dd_pd_accounting.ipynb
```

**Output**: Creates `data/outputs/datasheet/accounting_YYYYMMDD_HHMMSS.csv`

---

### **Step 3: Create Fixed-Name Links**

```bash
# Run helper script to create fixed-name copies
python3 scripts/link_latest_dd_outputs.py
```

**Output**:
```
✅ Market DD: market_20251011_033800.csv → dd_pd_market_results.csv
✅ Accounting DD: accounting_20251011_033900.csv → dd_pd_accounting_results.csv
```

---

### **Step 4: Run Validation**

```bash
# All paths now locked and consistent
python3 scripts/validate_instruction3.py \
  --equity_vol data/clean/equity_volatility_by_year.csv \
  --dd_market_new data/outputs/datasheet/dd_pd_market_results.csv \
  --dd_accounting_new data/outputs/datasheet/dd_pd_accounting_results.csv \
  --tier_diag data/clean/total_return_diagnostic.csv
```

---

## ✅ **Expected Validation Output**

### **[A] Convergence Rate**
```
year  size_bucket  conv_rate
2016  large        0.95
2018  large        0.96  ← Should be high now
...
```

### **[B] Distributions**
```
year  metric      mean    p50    p90    max
2018  DD_m new    13.45   12.3   19.2   31.2  ← Decreased from ~18
2018  DD_a new    16.78   15.1   24.3   42.1  ← Decreased from ~27
```

### **[C] 2018 Sample**
```
ticker_base  sigma_E_new  DD_m_new  DD_m_delta
JPM          0.2068       12.34     -6.11      ← Negative = improvement
BAC          0.2830       11.23     -5.55      ← Negative = improvement
...
```

### **[D] Status Codes**
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

## 📊 **What Changed:**

### **Before Corrections:**
- Peer medians included already-imputed values (circular)
- Output paths had timestamps (validator couldn't find them)

### **After Corrections:**
- Peer medians only from primary methods (monthly36, monthly_ewma)
- Fixed-name outputs created via helper script
- Validator paths locked and consistent

---

## 🎯 **Success Criteria:**

All checks must pass:
- ✅ **[A]**: Convergence >90%
- ✅ **[B]**: 2018 DD decreased 20-40%
- ✅ **[C]**: All DD_m_delta < 0 (negative)
- ✅ **[D]**: No "2018" flags
- ✅ **[E]**: Tier counts unchanged (1308/0/116)

---

## 📁 **File Status:**

### **Ready:**
- ✅ `data/clean/equity_volatility_by_year.csv` (updated with corrected peer median)
- ✅ `scripts/02_calculate_equity_volatility.py` (corrected)
- ✅ `scripts/link_latest_dd_outputs.py` (new helper)
- ✅ `scripts/validate_instruction3.py` (validator)

### **To Generate:**
- 📄 `data/outputs/datasheet/market_*.csv` (from notebook)
- 📄 `data/outputs/datasheet/accounting_*.csv` (from notebook)
- 📄 `data/outputs/datasheet/dd_pd_market_results.csv` (from helper)
- 📄 `data/outputs/datasheet/dd_pd_accounting_results.csv` (from helper)

---

## 🚀 **Quick Start Commands:**

```bash
# Navigate to project
cd /Users/guillaumebld/Documents/Graduate_Research/Professor\ Abol\ Jalilvand/fall2025/risk_bank/risk_bank

# Step 1 & 2: Run notebooks (use Jupyter UI)
jupyter notebook dd_pd_market.ipynb
jupyter notebook dd_pd_accounting.ipynb

# Step 3: Create fixed-name links
python3 scripts/link_latest_dd_outputs.py

# Step 4: Validate
python3 scripts/validate_instruction3.py \
  --equity_vol data/clean/equity_volatility_by_year.csv \
  --dd_market_new data/outputs/datasheet/dd_pd_market_results.csv \
  --dd_accounting_new data/outputs/datasheet/dd_pd_accounting_results.csv \
  --tier_diag data/clean/total_return_diagnostic.csv
```

---

## ✅ **READY TO EXECUTE**

All corrections applied. Paths locked. Validation ready.

**Next**: Run the 4 commands above in sequence.

---

*Prepared: October 11, 2025 at 3:38am*
