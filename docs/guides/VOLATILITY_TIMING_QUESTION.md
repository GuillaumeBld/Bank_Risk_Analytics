# Equity Volatility Computation Timing

**Question**: Is equity volatility computed before or after dropping variables with not enough debt?

**Answer**: **BEFORE - but actually, NO rows are dropped at all.**

---

## Key Finding: No Rows Are Dropped

### **Both notebooks (accounting and market) keep ALL rows**

Neither notebook drops rows based on debt criteria. Instead, they:
1. **Calculate σ_E for ALL observations** (regardless of debt status)
2. **Flag invalid observations** when calculating DD/PD
3. **Set DD/PD = NaN** for problematic rows
4. **Export everything** to CSV (including flagged rows)

---

## Workflow in dd_pd_accounting.ipynb

### **Section 5: Equity Volatility Calculation**
**Lines 335-513**

```python
# Compute sigma_E using returns up to t-1 only
df['sigma_E_tminus1'] = df.groupby('instrument', group_keys=False)['rit'].apply(rolling_sigma_prior)
df['sigma_E'] = df['sigma_E_tminus1']
```

**Status**: σ_E calculated for **ALL 1,425 rows** in dataset

**No filtering based on debt at this stage.**

---

### **Section 7: DD Calculation with Validation**
**Lines 584-626**

```python
# Define valid inputs
valid_inputs = df['E'].gt(0) & df['F'].gt(0) & valid_sigmaV & df['mu_hat'].notna()
                              ↑
                        Check F > 0 here

# Calculate DD using np.where
df['DD_naive'] = np.where(
    valid_inputs,          # If valid
    <DD formula>,          # Calculate DD
    np.nan,                # Else set to NaN
)
```

**What happens to rows where F <= 0:**
- σ_E was **already calculated** (in Section 5)
- DD_naive is set to **NaN** (not calculated)
- Row is **KEPT** in dataframe (not dropped)

---

### **Section 8: Flag Invalid Observations**
**Lines 634-797**

```python
# Flag problematic observations
nonpos_EF = (df['E'] <= 0) | (df['F'] <= 0)
df['naive_status'] = assign_status(...)  # "nonpos_EF", "ok", etc.
```

**Output**:
```
naive_status counts:
  insufficient_returns: 475
  nonpos_EF: 16        ← These have F <= 0
  ok: 934
```

**Critical**: 16 rows have `nonpos_EF` (non-positive E or F)
- These rows **still have σ_E calculated**
- Their DD_naive = NaN
- They are **kept in the output file**

---

### **Section 9: Export ALL Rows**
**Lines 805-1024**

```python
df[result_cols].to_csv(dd_output, index=False)
```

**All 1,425 rows exported**, including:
- 934 with valid DD (status = "ok")
- 475 with insufficient returns
- 16 with non-positive E or F

---

## Workflow in dd_pd_market.ipynb

### **Section 5: Load Pre-computed Equity Volatility**
**Lines 418-510**

```python
# Load equity volatility (already computed externally)
equity_vol = pd.read_csv('equity_volatility_by_year.csv')
df = df.merge(equity_vol, on=['ticker', 'year'], how='left')
```

**Status**: Equity volatility merged for all observations

---

### **Section 5.4: Validate Required Inputs**
**Lines 482-505**

```python
required_columns = ['instrument', 'year', 'market_cap', 'equity_volatility', 'rf', 'debt_total']

# Check for missing required inputs
invalid_rows = df[df[required_columns].isna().any(axis=1)]
if len(invalid_rows) > 0:
    print(f"[WARN] Dropping {len(invalid_rows)} rows with missing required inputs")
    df = df.dropna(subset=required_columns)
```

**THIS IS THE KEY DIFFERENCE:**

Market method **DOES drop rows** with missing debt_total, but:
1. Equity volatility is **already loaded/merged** before this check
2. Dropping happens **AFTER** volatility is in the dataframe
3. Only 2 rows dropped (COFS 2018, 2019)

---

## Timeline Comparison

### **Accounting Method**:
```
Step 1: Load data (1,425 rows)
Step 2: Calculate σ_E for all rows → All 1,425 have σ_E
Step 3: Calculate DD with validation (F > 0) → 16 get NaN
Step 4: Flag invalid rows → Status = "nonpos_EF"
Step 5: Export all 1,425 rows → Including flagged ones
```

**Result**: σ_E calculated **BEFORE** debt check, NO DROPPING

---

### **Market Method**:
```
Step 1: Load data (1,424 rows)
Step 2: Merge pre-computed σ_E → All 1,424 have σ_E
Step 3: Validate required columns → Drop 2 rows with missing debt
Step 4: Calculate DD via Merton solver → 1,422 remaining rows
Step 5: Export 1,422 rows
```

**Result**: σ_E merged **BEFORE** debt check, 2 ROWS DROPPED

---

## Summary Table

| Method | σ_E Calculation Timing | Debt Filtering | Rows Dropped | Invalid Rows in Output |
|--------|------------------------|----------------|--------------|------------------------|
| **Accounting** | Section 5 (early) | Section 7 (flags only) | **0** | Yes (16 with status flag) |
| **Market** | Section 5 (early) | Section 5.4 (actual drop) | **2** | No (already removed) |

---

## Answer to Your Question

### **Is equity volatility computed before or after dropping variables with not enough debt?**

**BEFORE** - in both methods:

1. **Accounting method**:
   - σ_E computed in Section 5
   - Debt check (F > 0) in Section 7
   - **BUT: No rows are dropped**, just flagged with NaN

2. **Market method**:
   - σ_E merged in Section 5
   - Debt validation/dropping in Section 5.4
   - 2 rows dropped (COFS 2018, 2019)

### **Why This Matters**

**For rolling window calculations**:
- σ_E uses 3-year rolling window of `rit`
- If a bank has debt issues in year t but valid data in t-1, t-2:
  - σ_{E,t} will still be calculated using historical returns
  - DD_t will be NaN (accounting) or row dropped (market)
  
**Example**: Bank with F <= 0 in 2020:
- 2018, 2019: F > 0, valid DD
- 2020: F <= 0
  - Accounting: σ_{E,2020} = std(rit_2017, rit_2018, rit_2019) ✓, DD_2020 = NaN
  - Market: σ_{E,2020} loaded ✓, but if debt_total missing → row dropped

---

## Practical Implications

### **1. Volatility is always available**
Even for "bad" observations, you can see what their equity volatility was.

### **2. Different philosophies**
- **Accounting**: Keep everything, flag issues → User decides what to exclude
- **Market**: Drop bad inputs upfront → Cleaner dataset, no NaNs

### **3. For your return data integration**
When you integrate new return data:
- Both methods will recalculate σ_E **before** any debt checks
- New `rit` values will flow through to σ_E for ALL observations
- Debt filtering happens **later** in the pipeline

---

## Verification

### **Check accounting method**:
```python
acct = pd.read_csv('data/outputs/datasheet/accounting.csv')

# Check rows with nonpos_EF status
bad_debt = acct[acct['naive_status'] == 'nonpos_EF']
print(f"Rows with F <= 0: {len(bad_debt)}")
print(f"These rows have sigma_E: {bad_debt['sigma_E'].notna().sum()}")
print(f"These rows have DD_a: {bad_debt['DD_a'].notna().sum()}")
```

**Expected output**:
```
Rows with F <= 0: 16
These rows have sigma_E: 16  ← σ_E calculated
These rows have DD_a: 0      ← DD not calculated
```

---

## Conclusion

✅ **Equity volatility is computed BEFORE debt validation**  
✅ **In accounting method: No rows are dropped** (just flagged with NaN)  
✅ **In market method: 2 rows dropped** (after σ_E is merged)  
✅ **Both methods ensure σ_E is available for ALL initial observations**

**Key takeaway**: The debt check is a **validation step during DD calculation**, not a **data filtering step before σ_E calculation**.

---

*Last updated: 2025-10-11*  
*Based on: dd_pd_accounting.ipynb and dd_pd_market.ipynb code inspection*
