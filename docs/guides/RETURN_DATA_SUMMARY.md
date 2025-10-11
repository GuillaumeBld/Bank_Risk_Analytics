# Total Return Data Summary - Executive Overview

**Date**: 2025-10-11  
**Analysis**: Return data coverage for 244 banks (2013-2023)

---

## 🎯 Key Findings

### Data Quality Overview

| Metric | Monthly | Annual |
|--------|---------|--------|
| **Banks** | 244 | 244 |
| **Years** | 2013-2023 | 2013-2024 |
| **Total Observations** | 31,946 | 2,906 |
| **Missing Values** | 3,459 (10.8%) | 310 (10.7%) |

---

## 📊 Monthly Coverage Analysis

### Coverage Breakdown (2,664 bank-years total)

| Coverage Level | Count | % | Status |
|---------------|-------|---|--------|
| **Complete (12 months)** | 2,334 | 87.6% | ✅ Excellent |
| **Good (9-11 months)** | 20 | 0.8% | ✅ Usable |
| **Partial (6-8 months)** | 30 | 1.1% | ⚠️ Needs backup |
| **Sparse (1-5 months)** | 24 | 0.9% | ❌ Insufficient |
| **No data (0 months)** | 256 | 9.6% | ❌ Missing |

---

## 🔄 Annual Backup Availability

### For bank-years with < 9 months of monthly data:

**Total incomplete cases**: 310 bank-years (11.6%)

| Category | Count | % of Incomplete |
|----------|-------|-----------------|
| **Has annual backup** | 9 | 2.9% |
| **No annual backup** | 301 | 97.1% |

### **Critical Finding**: 
⚠️ Annual backup is available for **only 9 out of 310** incomplete cases (2.9%)

**Reason**: Most incomplete monthly data cases are also missing in annual data (same underlying data gaps)

---

## 📋 Data Quality Tiers

### **Tier 1: Use Directly** ✅
- **Bank-years**: 2,354 (88.4%)
- **Criteria**: ≥ 9 months of valid monthly data
- **Action**: Use monthly returns as-is
- **Quality**: High

### **Tier 2: Needs Supplement** ⚠️
- **Bank-years**: 9 (0.3%)
- **Criteria**: < 9 months monthly + annual backup available
- **Action**: Use annual return to fill gaps
- **Quality**: Medium (requires adjustment)

### **Tier 3: Exclude** ❌
- **Bank-years**: 301 (11.3%)
- **Criteria**: < 9 months monthly + no annual backup
- **Action**: Exclude from analysis
- **Quality**: Insufficient

---

## 🔍 Worst Cases

### Banks with Consistent Missing Data

**Examples of banks with 0 monthly data across multiple years:**
- **AMTB**: Missing 2013-2022 (10 years)
- **AUB**: Missing 2013-2022 (10 years)
- **VABK**: Missing 2013-2020 (8 years)
- **BCML**: Missing 2013-2017 (5 years)

**Total worst cases** (< 6 months, no backup): **277 bank-years**

---

## 💡 Implications for Analysis

### Current Dataset Compatibility

Your current `esg_0718.csv` dataset has:
- **Years**: 2016-2023
- **Observations**: 1,424 bank-year pairs

### Impact of New Return Data

| Category | Count | Impact |
|----------|-------|--------|
| Can use directly | ~1,260 | ✅ Good coverage |
| Needs annual backup | ~5 | ⚠️ Manual review |
| Will be excluded | ~159 | ❌ Data loss |

**Estimated usable data**: ~88-90% of current dataset

---

## 📝 Next Steps

### 1. **Data Integration**
- [ ] Match return data with existing dataset by ticker
- [ ] Handle ticker suffixes (.N, .O, .OQ)
- [ ] Verify date alignment

### 2. **Quality Control**
- [ ] Review the 9 cases with annual backup
- [ ] Decide on monthly equivalent calculation (annual/12?)
- [ ] Set exclusion criteria for analysis

### 3. **Documentation**
- [ ] Document which banks/years are excluded
- [ ] Create data lineage tracking
- [ ] Update methodology section

### 4. **Validation**
- [ ] Compare new returns vs existing `rit` column
- [ ] Check for outliers
- [ ] Verify consistency

---

## 📂 Generated Files

1. **Full Documentation**: `docs/guides/return_data_coverage.md`
   - Complete list of all 310 incomplete cases
   - Detailed bank-year breakdown
   
2. **Detailed CSV**: `data/outputs/analysis/return_coverage_detailed.csv`
   - Machine-readable format
   - For further analysis

3. **Analysis Script**: `scripts/analyze_return_data_coverage.py`
   - Reusable for updated data
   - Can be re-run anytime

---

## ⚠️ Important Notes

1. **Annual backup is NOT a silver bullet**
   - Only 2.9% of incomplete cases have annual backup
   - Most data gaps exist in both monthly and annual files

2. **Missing data is systematic**
   - Some banks have no data for entire periods
   - Likely due to:
     - Mergers/acquisitions
     - Delisting
     - Data source limitations

3. **Quality over quantity**
   - 88.4% of data is high quality (Tier 1)
   - Better to exclude bad data than force-fit with backups

---

## 🎯 Recommendation

**Proceed with 3-tier approach**:
1. Use Tier 1 data directly (88.4%)
2. Manually review Tier 2 cases (9 banks) - decide case-by-case
3. Exclude Tier 3 data (11.3%)

**Expected final coverage**: ~88-90% of current dataset with high quality data

---

*For detailed breakdowns, see `return_data_coverage.md`*
