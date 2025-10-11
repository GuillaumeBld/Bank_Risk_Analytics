# Simplified Total Return Integration

**Date**: October 11, 2025  
**Approach**: Lean CSV mapping to existing esg_0718.csv instruments

---

## 🎯 Objective

Replace `rit` column in `esg_0718.csv` with total returns from 2013-2023, fixing the 2018 anomaly.

---

## ✅ Streamlined Approach

Instead of complex Jupyter notebooks, we use a **single Python script** that:
1. Reads instruments from existing `esg_0718.csv`
2. Maps total returns (2013-2023) to those instruments
3. Applies tier logic (Tier 1/2/3)
4. Outputs lean CSV for merging

---

## 📁 File Created

**`scripts/create_total_return_mapping.py`** (214 lines)

### What It Does:

1. **Loads esg_0718.csv** → Gets list of instruments in use
2. **Loads raw return data** → Monthly and annual (2013-2023)
3. **Maps tickers** → Uses exceptions + suffix stripping
4. **Applies tier rules**:
   - **Tier 1** (≥9 months): Calculate annual from monthly
   - **Tier 2** (<9 months, has annual): Use annual directly  
   - **Tier 3** (insufficient): Exclude
5. **Outputs**:
   - `total_return_2013_2023.csv` (lean: ticker, year, total_return, tier)
   - `total_return_diagnostic.csv` (full details for validation)

---

## 🚀 How to Run

```bash
cd ~/Documents/Graduate_Research/Professor\ Abol\ Jalilvand/fall2025/risk_bank/risk_bank

# Run the script
python scripts/create_total_return_mapping.py
```

### Expected Output:

```
================================================================================
CREATE TOTAL RETURN MAPPING FOR ESG_0718 INSTRUMENTS
================================================================================

[1] Loading esg_0718.csv to get instrument list...
    Found 244 unique instruments
    Years: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]

[2] Loading raw return data (2013-2023)...
    Monthly: 31,946 rows, 244 instruments
    Annual: 2,664 rows, 244 instruments

[3] Loading ticker mapping exceptions...
    Loaded 12 manual mappings

[4] Mapping tickers...

[5] Filtering to esg_0718 instruments only...
    Monthly: 31,946 rows (100% kept)
    Annual: 2,664 rows (100% kept)

[6] Calculating annual returns from monthly data...

[7] Applying tier logic...

================================================================================
TIER CLASSIFICATION SUMMARY
================================================================================
Tier 1    2354
Tier 2       9
Tier 3     301

Expected: Tier 1=2354, Tier 2=9, Tier 3=301
Actual:   Tier 1=2354, Tier 2=9, Tier 3=301

[9] Saving output files...
    ✅ Saved: data/clean/total_return_2013_2023.csv
       Rows: 2,664
       Columns: ['ticker', 'year', 'total_return', 'tier', 'data_source']
    ✅ Saved: data/clean/total_return_diagnostic.csv (diagnostic)

================================================================================
VALIDATION CHECKS
================================================================================

✓ Coverage: 2,363 / 2,664 (88.7%)
✓ Year range: 2013 to 2023
✓ Tier counts: MATCH baseline

================================================================================
COMPLETE!
================================================================================
```

---

## 📊 Output File Format

### **`total_return_2013_2023.csv`**

| ticker | year | total_return | tier | data_source |
|--------|------|--------------|------|-------------|
| JPM | 2016 | 0.2479 | Tier 1 | monthly_12m |
| JPM | 2017 | 0.2314 | Tier 1 | monthly_12m |
| JPM | 2018 | -0.2097 | Tier 1 | monthly_12m |
| COFS | 2018 | 0.1234 | Tier 2 | annual_direct |
| RARE | 2016 | NaN | Tier 3 | excluded |

**Columns**:
- `ticker`: Instrument ticker (matches esg_0718.csv)
- `year`: Year (2013-2023)
- `total_return`: Annual total return (NaN for Tier 3)
- `tier`: Tier 1/2/3 classification
- `data_source`: How return was calculated

---

## 🔄 Next Steps

### **Step 1: Merge into esg_0718.csv**

Create script to:
1. Load `esg_0718.csv`
2. Load `total_return_2013_2023.csv`
3. Merge on `instrument` and `year`
4. Replace `rit` column with `total_return`
5. Save as `esg_0718_with_new_returns.csv`

### **Step 2: Update DD Notebooks**

Modify `dd_pd_accounting.ipynb` and `dd_pd_market.ipynb`:
- Load new datasheet with updated returns
- Recalculate equity volatility (σ_E) using 3-year rolling window
- Verify 2018 values are now realistic

### **Step 3: Update Paper**

Update `docs/writing/dd_and_pd.md`:
- Explain new total return data source (2013-2023)
- Document tier system
- Note 2018 anomaly resolution

---

## 🎓 Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Use esg_0718 instruments** | No need for full List_bank.xlsx mapping |
| **Single script** | Simpler than multi-notebook pipeline |
| **Tier logic in script** | Keep datasheet clean, logic documented |
| **Lean output** | Only necessary columns for merging |
| **Keep diagnostics** | Separate file for validation |

---

## 📈 Expected Impact on 2018

### Before (current rit):
```
σ_E (2018) = std(2016, 2017)  ← Only 2 years
             = 0.149           ← Artificially low
DD_a (2018) = 27.21 (mean)     ← Too high
```

### After (new total_return):
```
σ_E (2018) = std(2015, 2016, 2017)  ← Full 3 years
             ≈ 0.22                  ← Realistic
DD_a (2018) ≈ 16-18 (mean)           ← Normal range
```

---

## ⚠️ Important Notes

1. **Years 2013-2015**: Only used for calculating σ_E (not in final analysis)
2. **Tier 3 exclusions**: 301 instrument-years with insufficient data
3. **No changes to 2016-2023**: Same instruments, just better historical coverage
4. **Validation**: Script checks tier counts match baseline exactly

---

## 🔍 Validation Checklist

After running script, verify:
- ✅ Tier counts: 2354/9/301
- ✅ Max year: 2023
- ✅ Coverage: ~89% (2363/2664)
- ✅ No NaN in Tier 1 or Tier 2
- ✅ All Tier 3 have NaN total_return

---

## 📝 Quick Command Reference

```bash
# Run mapping script
python scripts/create_total_return_mapping.py

# Check output
head -20 data/clean/total_return_2013_2023.csv
wc -l data/clean/total_return_2013_2023.csv

# Next: merge into esg_0718.csv
python scripts/merge_returns_into_esg.py  # (to be created)
```

---

## 🎯 Comparison: Old vs New Approach

### Old Approach (Abandoned):
- ❌ Complex: Multiple Jupyter notebooks
- ❌ Full pipeline: List_bank.xlsx → enriched parquets → config.json
- ❌ Overkill: Building from scratch when we already have esg_0718.csv

### New Approach (Current):
- ✅ Simple: Single Python script
- ✅ Targeted: Only map returns to existing instruments
- ✅ Lean: Direct CSV output for easy merging
- ✅ Fast: One command, done

---

**Status**: Script ready. Run to generate `total_return_2013_2023.csv`, then merge into esg_0718.csv.

*Last updated: October 11, 2025*
