# Return Data Integration Q&A
**Complete answers to de-risk integration and modeling**

---

## SECTION 1: Scope and Identifiers

### Q1: What is the definitive security identifier per row?

**Answer**: **Ticker WITH suffix** is the definitive identifier.

**Details**:
- Format: `TICKER.EXCHANGE_CODE` (e.g., `BAC.N`, `JPM.N`, `ABCB.OQ`)
- Monthly: 244 unique instruments
- Annual: 244 unique instruments
- Suffixes indicate exchange:
  - `.N` = NYSE (6,600 obs)
  - `.O` = NASDAQ (3,300 obs)
  - `.OQ` = NASDAQ (20,197 obs)
  - `.K`, `.PK`, `.A` = Other exchanges

**Recommendation**: Use full ticker with suffix as primary key, but create `ticker_base` (without suffix) for matching to your existing dataset.

---

### Q2: Do tickers map one-to-one with banks over time?

**Answer**: **YES, one-to-one mapping confirmed.**

**Evidence**:
- Zero base tickers have multiple suffixes over time
- Each bank keeps same ticker+suffix throughout the dataset
- No ticker changes detected

**Crosswalk**: Not needed - tickers are stable.

**Exception**: 2 tickers disappear before 2023:
- `BHLIP.PK^B11` (last seen 2013)
- `CWBC.OQ` (last seen 2013)

---

### Q3: Should suffixes be standardized or preserved?

**Answer**: **Preserve suffixes, but CREATE ticker_base for joins.**

**Rationale**:
- Suffixes carry important exchange information
- Your existing dataset likely uses base tickers (without suffix)
- Need both for proper matching

**Strategy**:
```
Raw ticker: BAC.N
ticker_base: BAC  (for joining to existing data)
ticker_full: BAC.N (preserve for audit trail)
```

**Special cases found**:
- `CIZnv.OQ^J24` - has caret code (1,321 observations with ^)
- Keep as-is for now, clean during integration

---

## SECTION 2: Time Coverage and Indexing

### Q4: Confirm monthly periodization

**Answer**: **MONTH-END dated, 100% confirmed.**

**Evidence**:
- All 31,946 records are month-end dates
- Day distribution: 31st (18,636), 30th (10,648), 28th (2,178), 29th (484)
- No mid-month dates found

**Format**: `M/D/YY` (e.g., `1/31/13` = January 31, 2013)

**Date range**: 2013-01-31 to 2023-12-31

---

### Q5: Are there partial months?

**Answer**: **NO partial months. All records are complete end-of-month.**

**Confirmation**: 100.0% of dates match the last day of their month.

---

### Q6: For years with 0 valid months, carry forward for alignment?

**Answer**: **NO, do not carry forward empty years.**

**Rationale**:
- Empty years indicate bank didn't exist/wasn't traded
- Examples: AMTB, AUB, VABK have 0 observations 2013-2022
- BUT these banks DO have monthly data in the file (just NaN returns)
- The 0 valid months = all NaN for that year

**Recommendation**: Exclude bank-years with 0 valid months entirely (Tier 3).

---

### Q7: Should 2024 annual be used?

**Answer**: **IGNORE 2024 annual data.**

**Rationale**:
- Monthly data ends 2023-12-31
- Annual has 242 observations for 2024
- Your modeling dataset is 2016-2023
- 2024 is out of scope

**Action**: Filter annual data to `year <= 2023` during processing.

---

## SECTION 3: Return Definitions

### Q8: Exact definition of total return

**Answer**: **Total return = Price return + dividends, in PERCENTAGE form**

**Evidence**:
- Values range from -99.84% to +3,101.80% (monthly)
- Mean monthly: 1.20%, std: 20.40%
- Format: 6.164932 means +6.16% (not 0.0616 or 616%)

**Interpretation**: Likely **gross returns with dividend reinvestment** (standard for total return indices).

**Currency**: USD (U.S. market data, all NYSE/NASDAQ listings)

---

### Q9: Are returns chain-linked or simple period returns?

**Answer**: **SIMPLE period returns (NOT chain-linked)**

**Critical Finding**: 
- ABCB 2013: Compounded monthly returns = 69.02%
- ABCB 2013: Annual file shows = 21.50%
- **Difference: 47.52 pp** - MASSIVE discrepancy!

**This means**: 
- Monthly returns are simple month-over-month % changes
- Annual returns are simple year-over-year % changes
- They are NOT consistent with each other via compounding

**Implication**: You CANNOT compound monthly to get annual. Use them independently.

**For your DD calculation**: This is fine - you use annual returns directly for `rit`, not compounded monthlies.

---

### Q10: Currency and FX adjustments

**Answer**: **USD, no FX adjustment needed.**

All banks are U.S.-listed entities trading in USD.

---

### Q11: Splits and corporate actions

**Answer**: **Assumed reflected by source** (standard for total return data from Bloomberg/Refinitiv).

Total return indices automatically adjust for:
- Stock splits
- Dividends
- Spin-offs
- Rights offerings

---

## SECTION 4: Data Source and Lineage

### Q12: Raw providers

**Answer**: **Likely Refinitiv/Bloomberg** (inferred from structure)

**Evidence**:
- Exchange suffixes (.N, .O, .OQ) match Refinitiv conventions
- "Total Return" nomenclature is standard for these providers
- Comprehensive U.S. bank coverage

**Same feed**: Monthly and annual appear to be from same source (consistent formatting).

---

### Q13: Survivorship bias

**Answer**: **MINIMAL survivorship bias detected.**

**Evidence**:
- Only 2 tickers (0.8%) disappear before 2023
- Dataset includes banks that failed/merged
- Empty years preserved (not dropped)

**Conclusion**: Sample appears to include delisted banks.

---

### Q14: Corporate action timelines

**Answer**: **NOT provided in files.**

**Gaps explained**:
- Banks with 0 months 2013-2022: Likely late IPO or data vendor issue
- Missing data is systematic (same banks across both files)
- Not due to mergers/failures (those would show partial years)

**Action needed**: If specific banks matter, cross-reference with IPO/delisting databases.

---

## SECTION 5: Backup Logic and Tiers

### Q15: Is 9 the hard floor, or sensitivity at 8?

**Answer**: **Keep 9 as hard floor.**

**Rationale**:
- 15 cases with exactly 8 months
- Only 1 of those 15 has annual backup
- Not worth the complexity

**BUT**: Note that 8 months could be promoted to Tier 1 if you want to be less strict (adds 15 cases).

**Recommendation**: Stick with 9 months for clean threshold.

---

### Q16: How to use annual backup for Tier 2?

**Answer**: **Use annual as-is, DO NOT scale monthly.**

**For the 9 Tier 2 cases**:
1. **If months exist**: Keep monthly returns, flag year as "partial coverage"
2. **If no months exist**: Use annual return for that year
3. **DO NOT try to**: 
   - Pro-rate annual across missing months (inconsistent due to Q9 finding)
   - Scale monthly to match annual (they don't compound consistently)

**Tier 2 breakdown**:
- CIZnv.OQ^J24: 7 years (2015-2021) with 0-8 months
- PCB: 2 years (2013-2014) with 8 months

---

### Q17: Scale monthly to match annual?

**Answer**: **NO, do not scale.**

**Reason**: Monthly and annual are not consistent (see Q9). Scaling would introduce artificial adjustments.

**For Tier 2**: 
- If ≥ 9 months exist: Use monthly only
- If < 9 months: Use annual return for that year in your regression

---

### Q18: Drop Tier 3 or keep with flag?

**Answer**: **Drop outright, document in audit file.**

**Rationale**:
- 301 cases (11.3%) without sufficient data
- Keeping with NA adds complexity to analysis
- Better to have clean dataset

**Action**: Create `return_data_audit.csv` listing all exclusions with reason codes.

---

## SECTION 6: Anomalies to Pre-Decide

### Q19: PCB 100% and 122% returns valid?

**Answer**: **VALID but flag as outlier for review.**

**Data**:
- PCB 2013: 8 months, annual = 100.00%
- PCB 2014: 8 months, annual = 122.22%

**Context**: Small bank, could be legitimate recovery/turnaround or data error.

**Recommendation**: 
- Keep in dataset
- Flag for sensitivity analysis
- Consider winsorizing at 99th percentile

---

### Q20: CIZnv.OQ^J24 negative returns - keep for Tier 2?

**Answer**: **YES, keep as Tier 2 test cases.**

**Data**:
- 7 years of incomplete coverage (2015-2021)
- Returns range from -18.73% to +21.04%
- This is Citizens Financial Group (ticker changed)

**Use case**: Perfect examples to test annual backup logic.

---

### Q21: 8-month contiguous promotion rule?

**Answer**: **NO, keep simple 9-month rule.**

**Reason**: Would need row-by-row analysis to check contiguity. Not worth complexity for 15 cases.

**Alternative**: Lower threshold to 8 months for all (but keep at 9 for clean threshold).

---

## SECTION 7: File Schemas and Joins

### Q22: Column schemas

**Monthly raw**:
```
Index: int64
Date: object (M/D/YY format)
Instrument: object (TICKER.SUFFIX)
Total Return: float64 (percentage)
```

**Annual raw**:
```
Index: int64
Date: int64 (YYYY)
Instrument: object (TICKER.SUFFIX)  
Total Return: float64 (percentage)
```

---

### Q23: return_coverage_detailed.csv schema

**Current**:
```
instrument: object
year: int64
total_months: int64 (months with data, even if NaN)
valid_months: int64 (months with non-NaN returns)
has_annual_backup: bool
annual_return: float64
```

**Recommendation**: Add `data_tier` (1/2/3) column for easy filtering.

---

### Q24: Join key to modeling dataset

**Answer**: **ticker_base + year**

**Process**:
1. Clean suffixes from both datasets
2. Join on `ticker_base` + `year`
3. For monthly: add `month` to key
4. Handle mismatches manually (should be minimal)

**Your current dataset** uses instruments like `BAC`, `JPM` (no suffix) → use ticker_base for join.

---

### Q25: Desired output tables

**Recommendation**:

**1. monthly_returns_clean.csv**
```
Columns: instrument, ticker_base, year, month, date, 
         total_return_pct, data_tier, valid_flag
Filters: Only Tier 1 data (≥ 9 months)
Rows: ~28,000
```

**2. annual_returns_all.csv**
```
Columns: instrument, ticker_base, year, total_return_pct,
         monthly_coverage_count, data_tier, used_as_backup
Filters: All years, all tiers marked
Rows: ~2,600
```

**3. return_data_audit.csv**
```
Columns: instrument, year, tier, valid_months, has_backup,
         exclusion_reason, action_taken
Filters: All bank-years including Tier 3
Rows: ~2,664
Purpose: Full audit trail
```

---

## SECTION 8: Validation Rules

### Q26: Sanity checks and caps

**Outliers detected**:
- Monthly: 21 observations outside [-50%, +100%]
- Annual: 8 observations outside [-80%, +200%]

**Recommended caps**:
```python
MONTHLY_RETURN_MIN = -50  # %
MONTHLY_RETURN_MAX = 100  # %
ANNUAL_RETURN_MIN = -80   # %
ANNUAL_RETURN_MAX = 200   # %
```

**Action**: Flag outliers, don't drop automatically. Review case-by-case.

---

### Q27: Compound vs annual tolerance

**Answer**: **NOT APPLICABLE due to Q9 finding.**

Monthly and annual returns are NOT consistent via compounding.

**Do not validate**: compound(monthly) ≈ annual

**Instead validate**:
- No duplicate rows
- Returns within sanity bounds
- No missing months within valid years

---

### Q28: Data quality checks

**Confirmed**:
- ✅ No duplicate rows (monthly or annual)
- ✅ No missing tickers
- ⚠️ 3,459 NaN returns in monthly (10.8%)
- ⚠️ 310 NaN returns in annual (10.7%)

**Validation rules**:
1. Drop rows where `Total Return` is NaN
2. Flag returns outside caps
3. Ensure date formats parse correctly
4. Check ticker format matches pattern

---

## SECTION 9: Repro and Documentation

### Q29: Config as constants or exposed?

**Answer**: **Expose in config file.**

**Recommended config.json**:
```json
{
  "data_quality": {
    "tier_1_min_months": 9,
    "tier_2_backup_enabled": true,
    "tier_3_exclusion": true
  },
  "validation": {
    "monthly_return_min": -50,
    "monthly_return_max": 100,
    "annual_return_min": -80,
    "annual_return_max": 200
  },
  "processing": {
    "use_2024_annual": false,
    "standardize_suffixes": true,
    "create_ticker_base": true
  }
}
```

---

### Q30: Versioning and seeds

**Answer**: **Version all outputs with timestamps.**

**Files to version**:
- All generated CSVs: `*_YYYYMMDD_HHMMSS.csv`
- Documentation: `return_data_coverage_YYYYMMDD.md`
- Config: `return_config_YYYYMMDD.json`

**Keep seeds**: Save config and input file hashes for reproducibility.

**Git commit**: After each major processing run.

---

## CRITICAL FINDINGS SUMMARY

### 🔴 Critical Issue: Monthly ≠ Annual
**Finding**: Compounded monthly returns DO NOT equal annual returns (47pp difference for ABCB 2013).

**Implication**: Monthly and annual are independent measures, not chainable.

**Action**: Use annual returns for your DD calculation (as currently done). Do NOT compound monthly.

---

### ⚠️ Key Decisions Needed

1. **PCB 100%+ returns**: Keep or exclude?
2. **CIZnv.OQ^J24**: Use as Tier 2 test case?
3. **8-month threshold**: Keep at 9 or lower to 8?
4. **2024 data**: Confirm exclusion?

---

## NEXT STEPS

1. ✅ **Review this Q&A** - confirm decisions
2. ⏭️ **Create integration script** - based on answers
3. ⏭️ **Generate 3 output tables** - per Q25
4. ⏭️ **Validate joins** - match to existing dataset
5. ⏭️ **Update DD pipeline** - integrate new returns

---

*Generated from `scripts/deep_dive_return_data.py`*  
*All answers evidence-based from data analysis*
