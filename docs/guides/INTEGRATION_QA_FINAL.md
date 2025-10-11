# Return Data Integration Q&A - FINAL SPEC
**Post-List_bank.xlsx Analysis**

**Date**: 2025-10-11  
**Purpose**: Final specification for coder agent integration

---

## FILE STRUCTURE SUMMARY

### List_bank.xlsx (Authoritative Ticker Mapping)
- **Rows**: 244 banks
- **Key columns**:
  - `Ticker`: Base ticker (e.g., BAC, JPM) - **PRIMARY IDENTIFIER**
  - `Company`: Full company name
  - `Symbol`: Same as Ticker
  - `Listed/delisted (as of today)`: 234 listed, 10 delisted
  - `Reason`: Corporate action details (mergers, acquisitions)
  - `new ticker`: Post-merger ticker (10 cases)
  - `PermId`: Refinitiv Permanent ID (242 non-null)

### Return Data Files
- **Monthly**: 31,946 observations, 244 unique instruments
- **Annual**: 2,906 observations, 244 unique instruments
- **Instrument format**: `TICKER.SUFFIX` (e.g., BAC.N, JPM.N)

### Reconciliation Results
- **Perfect match on base ticker**: 232/244 (95.1%)
- **Mismatches**: 12 due to suffix variations and ticker changes

---

## ✅ ANSWERS TO 8 INTEGRATION QUESTIONS

### 1. Identifier Alignment

#### a) One-to-one correspondence?

**Answer**: **NO, not one-to-one on full instrument. YES on ticker_base.**

**Details**:
- **List_bank.xlsx** uses: `BAC`, `JPM`, `CIZN` (clean base tickers)
- **Return data** uses: `BAC.N`, `JPM.N`, `CIZnv.OQ^J24` (with suffixes)

**Matching results**:
- 232/244 match perfectly when suffixes are stripped
- 12 mismatches due to:
  1. **Suffix variations**: `BHLIP.PK` vs `BHLB`, `CIZnv.OQ` vs `CIZN`
  2. **Ticker change**: `MCHB` (new) vs `HMST` (old) post-merger
  3. **Minor differences**: Spelling, caret codes

#### b) Join on full instrument or ticker_base?

**Answer**: **Join on ticker_base (cleaned).**

**Rationale**:
- List_bank.xlsx is authoritative with clean tickers
- Return data has exchange suffixes that must be stripped
- After cleaning, 95% match rate

**Join strategy**:
```python
# Clean return data instruments
return_data['ticker_base'] = return_data['Instrument'].str.replace(r'(\.[A-Z]+|\^.*)$', '', regex=True).str.upper()

# Join to List_bank
merged = return_data.merge(
    list_bank,
    left_on='ticker_base',
    right_on='Ticker',
    how='left'
)
```

**Handle 12 mismatches**:
- Create manual mapping table for exceptions
- Or: Use PermId for cross-referencing

#### c) Propagate both or only ticker_base?

**Answer**: **Propagate BOTH in all outputs.**

**Columns to include**:
- `instrument`: Full original ticker with suffix (e.g., `BAC.N`)
- `ticker_base`: Cleaned ticker from List_bank (e.g., `BAC`)
- `company`: Full company name from List_bank
- `perm_id`: Refinitiv ID for cross-referencing

**Rationale**: 
- `instrument` for audit trail and data lineage
- `ticker_base` for joins to your existing modeling dataset
- `company` for readability
- `perm_id` for future integration with other data sources

---

### 2. Coverage Validation

**Answer**: **YES, return_coverage_detailed.csv is authoritative for tiering.**

**Confirmation**:
- ✅ `valid_months` column defines tier eligibility
- ✅ `has_annual_backup` column determines Tier 2 classification
- ✅ Generated from actual monthly data counts (not assumptions)

**For 0-month years**:
- **Action**: **Drop from all downstream aggregates** (not just mark as Tier 3)
- **Reason**: No data = cannot calculate returns
- **Exception**: Keep in audit file with `exclusion_reason = "no_data"`

**Implementation**:
```python
# Tier 1: Keep
tier1 = coverage[coverage['valid_months'] >= 9].copy()

# Tier 2: Keep with flag
tier2 = coverage[(coverage['valid_months'] < 9) & (coverage['has_annual_backup'] == True)].copy()

# Tier 3: Exclude from analysis, keep in audit only
tier3 = coverage[(coverage['valid_months'] < 9) & (coverage['has_annual_backup'] == False)].copy()
```

---

### 3. Time Span

#### Exclude 2024?

**Answer**: **YES, exclude all 2024 data.**

**Filters to apply**:
```python
monthly_clean = monthly[monthly['date_parsed'].dt.year <= 2023]
annual_clean = annual[annual['Date'] <= 2023]
```

**Reason**: Your modeling dataset is 2016-2023.

#### Month-end dated and sequential?

**Answer**: **YES, 100% month-end dated. NO duplicates found.**

**Validation results**:
- ✅ All 31,946 monthly records are month-end
- ✅ 0 duplicate (instrument, date) pairs
- ⚠️ Some banks have gaps (missing months within years)

**Skips within valid years**:
- Some banks have non-contiguous months (e.g., missing Feb in a year)
- This is already captured by `valid_months < 12`
- Acceptable if `valid_months >= 9`

---

### 4. Return Handling

#### Returns in percentage form everywhere?

**Answer**: **YES, all returns are in percentage form (not decimals).**

**Confirmed**:
- ✅ List_bank.xlsx: No return data (just ticker mapping)
- ✅ Monthly return data: Percentages (6.16 = +6.16%)
- ✅ Annual return data: Percentages (21.50 = +21.50%)

#### Convert to decimals for modeling?

**Answer**: **YES, convert for DD calculation.**

**Your DD formula** requires decimal returns:
```python
# Current practice (keep this)
r = annual_return_pct / 100  # Convert 21.50 to 0.2150
mu_hat = r  # Drift proxy in decimal form
```

**Output files**: Store as **percentages** (human-readable), convert in modeling script.

**Validation**: Include both forms in audit file:
- `total_return_pct`: 21.50 (for readability)
- `total_return_decimal`: 0.2150 (for validation)

---

### 5. Tier Rules

#### Still enforce ≥ 9 months?

**Answer**: **YES, keep 9 months as Tier 1 floor.**

**Final tier rules**:

**Tier 1** (Use directly):
- Criteria: `valid_months >= 9`
- Count: 2,354 bank-years (88.4%)
- Action: Use monthly returns as-is (primary data)

**Tier 2** (Annual backup):
- Criteria: `valid_months < 9 AND has_annual_backup == True`
- Count: 9 bank-years (0.3%)
- Action: Use annual return for that bank-year
- Banks: CIZnv.OQ^J24 (7 years), PCB (2 years)

**Tier 3** (Exclude):
- Criteria: `valid_months < 9 AND has_annual_backup == False`
- Count: 301 bank-years (11.3%)
- Action: Drop from analysis, document in audit

#### PCB 100%+ returns - keep or exclude?

**Answer**: **KEEP, flag for sensitivity analysis.**

**Details**:
- PCB 2013: 8 months, annual = 100.00%
- PCB 2014: 8 months, annual = 122.22%

**Actions**:
1. Keep in dataset (legitimately high returns possible for small banks)
2. Add `return_flag = "outlier_high"` column
3. Document in sensitivity section
4. Consider winsorizing at 99th percentile for robustness checks

#### Config file for reproducibility?

**Answer**: **YES, create config.json with all thresholds.**

**Recommended structure**:
```json
{
  "version": "1.0.0",
  "generated_date": "2025-10-11",
  
  "tier_rules": {
    "tier_1_min_months": 9,
    "tier_2_backup_enabled": true,
    "tier_3_exclude": true
  },
  
  "validation": {
    "monthly_return_min_pct": -50,
    "monthly_return_max_pct": 100,
    "annual_return_min_pct": -80,
    "annual_return_max_pct": 200,
    "flag_not_drop": true
  },
  
  "time_span": {
    "monthly_year_min": 2013,
    "monthly_year_max": 2023,
    "annual_year_min": 2013,
    "annual_year_max": 2023,
    "exclude_2024": true
  },
  
  "identifiers": {
    "use_ticker_base_join": true,
    "preserve_full_instrument": true,
    "manual_mapping_file": "data/clean/ticker_mapping_exceptions.csv"
  }
}
```

---

### 6. Output Schema Confirmation

**Answer**: **YES, three files with BOTH instrument and ticker_base in each.**

#### File 1: monthly_returns_clean.csv (Tier 1 only)

**Columns**:
```
instrument          # Full ticker with suffix (e.g., BAC.N)
ticker_base         # Clean ticker from List_bank (e.g., BAC)
company             # Company name from List_bank
perm_id             # Refinitiv PermId
year                # 2013-2023
month               # 1-12
date                # YYYY-MM-DD (month-end)
total_return_pct    # Return in percentage (6.16)
total_return_decimal # Return in decimal (0.0616)
data_tier           # Always 1
valid_months_in_year # Count of valid months for that year
return_flag         # "normal", "outlier_high", "outlier_low", "missing"
```

**Filters applied**:
- `valid_months >= 9`
- `year <= 2023`
- `total_return_pct IS NOT NULL`

**Estimated rows**: ~28,000

---

#### File 2: annual_returns_all.csv (All tiers)

**Columns**:
```
instrument          # Full ticker with suffix
ticker_base         # Clean ticker from List_bank
company             # Company name
perm_id             # Refinitiv PermId
year                # 2013-2023
total_return_pct    # Annual return in percentage
total_return_decimal # Annual return in decimal
data_tier           # 1, 2, or 3
monthly_coverage_count # Valid months in that year
has_annual_backup   # TRUE/FALSE
used_as_backup      # TRUE if Tier 2 and no monthly data used
return_flag         # "normal", "outlier_high", "outlier_low"
exclusion_reason    # NULL for Tier 1-2, reason for Tier 3
```

**Filters applied**:
- `year <= 2023`
- All tiers included with flags

**Estimated rows**: ~2,600

---

#### File 3: return_data_audit.csv (Full audit trail)

**Columns**:
```
instrument          # Full ticker with suffix
ticker_base         # Clean ticker from List_bank
company             # Company name
year                # 2013-2023
data_tier           # 1, 2, or 3
valid_months        # Count of valid monthly returns
has_annual_backup   # TRUE/FALSE
annual_return_pct   # If available
monthly_return_min  # Min monthly return for that year
monthly_return_max  # Max monthly return for that year
monthly_return_mean # Mean monthly return
exclusion_reason    # "no_data", "insufficient_months", "no_backup", NULL
action_taken        # "included", "used_annual", "excluded"
notes               # Any special handling notes
```

**Filters applied**: None - full audit of all 2,664 bank-years

**Purpose**: Complete audit trail for paper methodology section

---

### 7. Validation Thresholds

#### Keep caps as defined?

**Answer**: **YES, flag not drop.**

**Thresholds**:
```python
MONTHLY_RETURN_MIN = -50   # %
MONTHLY_RETURN_MAX = 100   # %
ANNUAL_RETURN_MIN = -80    # %
ANNUAL_RETURN_MAX = 200    # %
```

**Action on outliers**:
- **Do NOT drop** automatically
- **Flag** with `return_flag` column
- **Document** in audit file

**Outlier counts**:
- Monthly: 21 observations (0.07%)
- Annual: 8 observations (0.31%)

#### Outlier flag column name?

**Answer**: **Use `return_flag` with standard values.**

**Possible values**:
- `"normal"`: Within caps
- `"outlier_high"`: Above upper cap
- `"outlier_low"`: Below lower cap
- `"missing"`: NULL/NaN (for completeness in monthly)

**Implementation**:
```python
def flag_return(value, min_cap, max_cap):
    if pd.isna(value):
        return 'missing'
    elif value < min_cap:
        return 'outlier_low'
    elif value > max_cap:
        return 'outlier_high'
    else:
        return 'normal'
```

---

### 8. Integration Readiness

**Answer**: **Load List_bank.xlsx FIRST, merge during tiering process.**

**Workflow**:

#### Step 1: Load and prepare List_bank.xlsx
```python
list_bank = pd.read_excel('data/clean/List_bank.xlsx')
list_bank['ticker_base'] = list_bank['Ticker'].str.upper()
```

#### Step 2: Clean return data identifiers
```python
monthly['ticker_base'] = monthly['Instrument'].str.replace(
    r'(\.[A-Z]+|\^.*)$', '', regex=True
).str.upper()
```

#### Step 3: Merge BEFORE tiering
```python
monthly_enriched = monthly.merge(
    list_bank[['ticker_base', 'Company', 'PermId', 
               'Listed/delisted (as of today)', 'Reason', 'new ticker']],
    on='ticker_base',
    how='left',
    indicator=True
)
```

#### Step 4: Handle merge mismatches
```python
# Check for unmatched returns
unmatched = monthly_enriched[monthly_enriched['_merge'] == 'left_only']
print(f'Unmatched return records: {len(unmatched)}')

# Create manual mapping for 12 exceptions
manual_map = {
    'BHLIP.PK': 'BHLB',
    'BRKL.O': 'BRKL',
    'CIZNV.OQ': 'CIZN',
    'DFS.N': 'DFS',
    'EBTC.OQ': 'EBTC',
    'EVBN.K': 'EVBN',
    'FLIC.OQ': 'FLIC',
    'GNTY.K': 'GNTY',
    'MCHB': 'HMST',  # Post-merger ticker
    'OPOF.O': 'OPOF',
    'PPBI.O': 'PPBI',
    'PWOD.O': 'PWOD'
}

# Apply manual mapping to unmatched
for return_tick, list_tick in manual_map.items():
    mask = monthly_enriched['ticker_base'] == return_tick
    match_data = list_bank[list_bank['ticker_base'] == list_tick].iloc[0]
    monthly_enriched.loc[mask, 'Company'] = match_data['Company']
    monthly_enriched.loc[mask, 'PermId'] = match_data['PermId']
    monthly_enriched.loc[mask, 'ticker_base'] = list_tick
```

#### Step 5: Apply tier rules with enriched data

#### Step 6: Generate three output files

**Why merge first**: 
- Ensures company names and PermIds propagate to all outputs
- Enables filtering by delisting status if needed
- Maintains data lineage throughout

---

## CRITICAL INTEGRATION NOTES

### 🔴 Manual Mapping Required

**12 instruments need manual mapping**:

| Return Data Instrument | List_bank Ticker | Reason |
|------------------------|------------------|--------|
| BHLIP.PK | BHLB | Suffix variation |
| BRKL.O | BRKL | Suffix present |
| CIZNV.OQ | CIZN | Spelling variation |
| DFS.N | DFS | Suffix present |
| EBTC.OQ | EBTC | Suffix present |
| EVBN.K | EVBN | Suffix present |
| FLIC.OQ | FLIC | Suffix present |
| GNTY.K | GNTY | Suffix present |
| **MCHB** | **HMST** | **Ticker changed post-merger** |
| OPOF.O | OPOF | Suffix present |
| PPBI.O | PPBI | Suffix present |
| PWOD.O | PWOD | Suffix present |

**Action**: Create `ticker_mapping_exceptions.csv` with these mappings.

---

### ⚠️ Corporate Actions Impact

**10 banks have corporate actions**:
- Mergers: 9 banks (with new tickers)
- Delisting: 1 bank (CIZN moved to OTCQX)

**Timeline data available**: `MM/YY` column in List_bank.xlsx (6 non-null values)

**Recommendation**: 
- Document merger dates in audit file
- Flag if merger occurred mid-year (affects return calculations)
- Consider excluding merger year for affected banks

---

### ✅ Data Quality Confirmed

- **No duplicate rows** in any file
- **100% month-end dates** in monthly data
- **244/244 banks present** in both return data and List_bank
- **95% automatic match rate** on ticker_base

---

## IMPLEMENTATION CHECKLIST

- [ ] Load List_bank.xlsx and prepare ticker_base
- [ ] Apply manual mapping for 12 exceptions
- [ ] Merge to return data BEFORE tiering
- [ ] Apply tier rules per Q5
- [ ] Convert returns to decimals for modeling
- [ ] Flag outliers per Q7
- [ ] Generate 3 output files per Q6
- [ ] Save config.json with thresholds
- [ ] Document 301 Tier 3 exclusions
- [ ] Validate output row counts match expectations
- [ ] Cross-check sample bank-years manually
- [ ] Generate integration summary report

---

## EXPECTED OUTCOMES

**After integration**:
- **Tier 1**: 2,354 bank-years (88.4%) ready for modeling
- **Tier 2**: 9 bank-years (0.3%) with annual backup
- **Tier 3**: 301 bank-years (11.3%) excluded with documentation
- **Total**: 2,664 bank-years fully documented

**Join success rate**:
- 100% after manual mapping applied
- All 244 banks from List_bank matched to return data

**Data loss**:
- ~11% excluded due to insufficient data (Tier 3)
- Acceptable given data quality standards

---

## READY FOR AGENT CODER

All 8 questions answered with concrete specifications.

**Proceed with integration using this spec.**

---

*Generated: 2025-10-11*  
*Based on: List_bank.xlsx + return data files + coverage analysis*
