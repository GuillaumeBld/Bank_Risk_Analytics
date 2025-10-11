# Datasheet Directory File Guide

**Location**: `data/outputs/datasheet/`

## 📋 Essential Files (Always Keep)

### 1. **accounting.csv** (307 KB)
- **Source**: `dd_pd_accounting.ipynb`
- **Contains**: Accounting-based DD/PD calculations
- **Columns**: 
  - DD calculations using balance sheet data
  - Volatility estimates (sigma_E, sigma_V_hat)
  - Drift proxies (mu_hat)
  - Status flags
- **Used by**: `merging.ipynb`

### 2. **market.csv** (788 KB)
- **Source**: `dd_pd_market.ipynb`
- **Contains**: Market-based DD/PD calculations (Merton model)
- **Columns**:
  - DD/PD from iterative solver
  - Asset values (V) and volatilities (sigma_V)
  - Convergence diagnostics
  - Status flags
- **Used by**: `merging.ipynb`

### 3. **merged.csv** (1,083 KB)
- **Source**: `merging.ipynb`
- **Contains**: Combined accounting + market + ESG data
- **Purpose**: Intermediate file before trimming
- **Used by**: `trim.ipynb` (if implemented)

### 4. **esg_0718.csv** (545 KB)
- **Source**: `merging.ipynb` (final output)
- **Contains**: **FINAL DATASET** for analysis
- **Observations**: 1,424 bank-year pairs (2016-2023)
- **Columns**:
  - DD_a, PD_a (accounting approach)
  - DD_m, PD_m (market approach)
  - ESG scores (environmental, social, governance)
  - Financial controls (assets, leverage, etc.)
  - Status flags (for exclusions/trimming)
- **Used by**: `analysis.ipynb` and your regressions

## 🔧 Optional Files

### **dd_pd_naive_config.json** (0.1 KB)
- Configuration file for DD calculations
- Contains parameters (T=1, r_f values, etc.)
- Safe to keep

### **esg_0718_backup.csv** (548 KB)
- Backup from duplicate fix (2025-10-08)
- Can be removed after verifying esg_0718.csv is correct

## 📦 Archived Files

**Location**: `archive/data_archive/`

These are old timestamped runs (from 2025-10-04):
- `accounting_20251004_041436.csv`
- `market_20251004_050613.csv`
- `merged_20251004_051328.csv`
- `esg_dd_pd_20251004_051328.csv`

**Purpose**: Historical reference, can be deleted if storage is needed

## 🔄 Data Pipeline Flow

```
Raw Data
   ↓
[dd_pd_accounting.ipynb] → accounting.csv
   ↓
[dd_pd_market.ipynb] → market.csv
   ↓
[merging.ipynb] → merged.csv → esg_0718.csv (FINAL)
   ↓
[analysis.ipynb] ← Uses esg_0718.csv
```

## 📊 Which File to Use?

**For analysis**: Always use **`esg_0718.csv`**

This is your final, cleaned dataset with:
- ✓ Duplicate PNC 2018 rows removed
- ✓ Low-leverage banks excluded (TD/TA < 2%)
- ✓ Extreme values trimmed (year-size percentiles)
- ✓ All ESG and financial controls included
- ✓ Status codes for tracking exclusions

## 🧹 Cleaning Policy

**Auto-generated files** from notebooks use timestamps and are archived automatically.

**Keep only**:
1. accounting.csv
2. market.csv
3. merged.csv
4. esg_0718.csv

**Archive** (move to `archive/data_archive/`):
- All files with `_YYYYMMDD_HHMMSS` timestamps

**Remove** (safe to delete):
- Very old backups (> 1 month)
- Duplicate files

## 📝 Notes

- The directory is cleaned by `scripts/cleanup_datasheet.py`
- Latest run always overwrites the 4 essential files
- Timestamped files are created during notebook execution but should be archived
- Total size for 4 essential files: ~2.7 MB

---
*Last updated: 2025-10-11*
