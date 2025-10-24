# Paper Update Summary - Descriptive Statistics Added

**Date**: October 14, 2025  
**Update**: Comprehensive descriptive statistics tables added to documentation

---

## ✅ What Was Updated

### Main Documentation File: `dd_and_pd.md`

Added a new section: **"Descriptive Statistics: DD and PD Measures"**

This section includes:

---

## 📊 Table 1: Overall Descriptive Statistics (Complete with All Percentiles)

**Key Statistics** (1,424 bank-years, 2016-2023):

| Metric | DD_a | DD_m | PD_a | PD_m |
|--------|------|------|------|------|
| **N** | **1,343** | **1,341** | 1,343 | 1,341 |
| **Mean** | 11.809 | 6.960 | 0.000855 | 0.001506 |
| **Median** | 11.238 | 6.361 | 0.000000 | 0.000000 |
| **Std Dev** | 5.512 | 3.699 | 0.027 | 0.009 |
| **90th %ile** | 17.818 | 10.497 | 0.000000 | 0.000604 |
| **95th %ile** | 20.789 | 13.118 | 0.000007 | 0.007102 |
| **99th %ile** | 27.680 | 20.714 | 0.001153 | 0.033134 |

**All percentiles included**: 1st, 5th, 10th, 25th, 50th (median), 75th, 90th, 95th, 99th

---

## 📊 Table 2: Statistics by Year

Shows temporal variation across 2016-2023:
- **2020 (COVID)**: Highest DD (14.49) - banks remained safe
- **2021**: Anomalous drop (DD=5.36) - under investigation
- **2022-2023**: Return to normal (DD~11.7-11.9)

---

## 📊 Table 3: Statistics by Bank Size

**Counterintuitive finding**:
- **Large banks**: DD_a = 9.19 (HIGHER risk)
- **Small banks**: DD_a = 11.93 (LOWER risk)

Contradicts "too big to fail" - suggests large banks have higher leverage or more complex risk profiles.

---

## 📊 Table 4: Correlation Matrix

**Key finding**: DD_a and DD_m correlation = **0.950** (validates both methods!)

---

## 🔍 N Difference Explanation ADDED

**Question Answered**: "Why does DD_a have 1,343 observations but DD_m has 1,341?"

**Answer**: 2-observation difference due to:
- **COFS 2018 and 2019** have accounting data but missing market cap
- Likely delisted or merged during these years
- **This is normal**: Market data has slightly lower coverage than accounting data
- DD_a uses book equity (balance sheet) → More complete
- DD_m uses market cap (stock price) → Requires active trading

---

## 📝 Results Section Text UPDATED

Added comprehensive interpretation paragraphs ready for your paper:

### Paragraph 1: Sample Overview
- Final sample: 1,424 observations
- Coverage: 94.3% (DD_a), 94.2% (DD_m)
- Explains 2-observation difference

### Paragraph 2: Risk Levels
- Mean DD: 11.81 (accounting), 6.96 (market)
- Mean PD: 0.09% (accounting), 0.15% (market)
- Distribution: 75% have PD ≈ 0 (very safe banks)
- Only top 5% show elevated risk

### Paragraph 3: Method Validation
- Correlation 0.950 validates both approaches
- DD_a > DD_m consistently (accounting more conservative)
- Book values more stable than market values

### Paragraph 4: Temporal Patterns
- Pre-COVID stable (2016-2019)
- COVID resilience (2020)
- 2021 anomaly noted
- Post-COVID normalization (2022-2023)

### Paragraph 5: Size Effects
- Unexpected: Large banks riskier than small
- Contrasts with "too big to fail"
- Possible explanations provided

### Paragraph 6: Volatility Methodology
- Daily returns, 252-day window
- Mean 31.7% (+17% vs monthly method)
- Coverage: 93.1% with all major banks complete
- Bharath & Shumway (2008) standard

---

## 📄 LaTeX Tables Available

**File**: `docs/writing/DESCRIPTIVE_TABLES_LATEX.txt`

Contains copy-paste ready LaTeX code for:
1. Table 1: Overall statistics
2. Table 2: Statistics by year
3. Table 3: Statistics by size
4. Table 4: Correlation matrix
5. **BONUS**: Combined panel table (space-saving version)

All tables professionally formatted with proper notes and citations.

---

## 🎯 How to Use in Your Paper

### Step 1: Copy Tables
Open `DESCRIPTIVE_TABLES_LATEX.txt` and copy the LaTeX code for the tables you want.

**Recommended for paper**:
- **Table 1**: Overall statistics (ESSENTIAL)
- **Table 2**: By year (RECOMMENDED - shows COVID period)
- **Table 3**: By size (OPTIONAL - interesting finding)
- **Table 4**: Correlation (OPTIONAL - can report in text)

**Alternative**: Use the combined panel table if space is limited.

### Step 2: Copy Results Text
From `dd_and_pd.md` section "Reporting in Your Paper", copy the updated results paragraphs (6 paragraphs covering all aspects).

### Step 3: Add to Discussion
Use the interpretations provided:
- Right-skewed distribution (most banks very safe)
- DD_a > DD_m pattern (accounting conservative)
- 2021 anomaly (acknowledge and investigate)
- Size effect (counterintuitive, discuss)
- Daily volatility advantage (better crisis capture)

---

## 📊 Key Numbers to Cite

**Sample**:
- 1,424 bank-year observations (2016-2023)
- 1,343 with DD_a (94.3%)
- 1,341 with DD_m (94.2%)
- 244 unique banks

**Risk Levels**:
- Mean DD_a: 11.81, DD_m: 6.96
- Mean PD_a: 0.09%, PD_m: 0.15%
- Median PD ≈ 0 (75th percentile still zero)

**Correlation**:
- DD_a vs DD_m: 0.950 (very high)
- Validates both methodologies

**Volatility**:
- Daily method: 31.7% mean
- Monthly method: 27.0% mean (old)
- Increase: +17.4%
- Coverage: 93.1%

**Temporal**:
- Pre-COVID (2016-2019): DD 12.7-13.7
- COVID (2020): DD 14.5 (resilient)
- 2021: DD 5.4 (anomaly)
- Post-COVID (2022-2023): DD 11.7-11.9

**Size**:
- Large: DD 9.19
- Mid: DD 10.73
- Small: DD 11.93
- Pattern: Large riskier than small (unexpected!)

---

## ✅ Quality Checks Completed

1. ✅ All percentiles calculated (1, 5, 10, 25, 50, 75, 90, 95, 99)
2. ✅ N difference explained (COFS 2018-2019 missing market data)
3. ✅ Tables formatted professionally
4. ✅ LaTeX code ready for paper
5. ✅ Interpretation paragraphs written
6. ✅ All major findings highlighted
7. ✅ Anomalies acknowledged (2021)
8. ✅ Citations included (Bharath & Shumway 2008)

---

## 📁 Files You Now Have

### Documentation
1. **`dd_and_pd.md`** - UPDATED with full descriptive statistics section
2. **`DESCRIPTIVE_STATISTICS_DD_PD.md`** - Detailed analysis with all tables
3. **`DESCRIPTIVE_TABLES_LATEX.txt`** - Copy-paste LaTeX code
4. **`DATA_COVERAGE_DISCLOSURE.md`** - Volatility coverage disclosure
5. **`PAPER_UPDATE_SUMMARY.md`** - This file

### Data
- **Latest dataset**: `esg_dd_pd_20251014_022322.csv` (1,424 obs)
- **Volatility file**: `equity_volatility_by_year_DAILY.csv` (1,955 obs, 93.1% with data)

---

## 🎯 What to Do Next

### For Your Paper:

1. **Open** `docs/writing/DESCRIPTIVE_TABLES_LATEX.txt`
2. **Copy** Table 1 (Overall Statistics) - paste into your paper
3. **Copy** Table 2 (By Year) - paste into your paper
4. **Read** the updated "Results Section" text in `dd_and_pd.md`
5. **Copy** the 6 results paragraphs into your paper's results section
6. **Adjust** wording to fit your paper's style
7. **Done!** Your paper now has complete descriptive statistics

### Optional Enhancements:

- **Investigate 2021 anomaly**: Why did DD drop so sharply?
- **Size analysis**: Explore why large banks show higher risk
- **Crisis analysis**: Deep dive into 2020 COVID period
- **Volatility comparison**: Show daily vs monthly differences

---

## 📊 Summary Statistics Quick Reference

**Your paper can now report**:
- ✅ Complete sample description (N, coverage)
- ✅ Central tendency (mean, median)
- ✅ Distribution shape (percentiles, skewness)
- ✅ Temporal variation (by year, COVID effects)
- ✅ Cross-sectional variation (by size)
- ✅ Method validation (correlation 0.950)
- ✅ Methodology upgrade (daily vs monthly volatility)

**All backed by professional tables with proper notes and citations.**

---

## 🎉 Paper Update Complete!

Your documentation now includes:
- 4 comprehensive descriptive tables
- Complete percentile distributions
- N difference explanation
- Ready-to-use results section text
- Copy-paste LaTeX code
- Professional formatting

**Everything is ready for your paper!** 📝✨

---

**Last Updated**: October 14, 2025 02:35 AM  
**Files Modified**: 5 documentation files  
**Tables Created**: 4 main tables + 1 combined panel table  
**LaTeX Code**: Ready for copy-paste  
**Status**: ✅ **COMPLETE**
